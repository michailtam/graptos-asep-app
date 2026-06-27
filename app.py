import streamlit as st
import pandas as pd
import pdfplumber
import os
import random
import re
import json
import time
import io
from streamlit_gsheets import GSheetsConnection

# --- ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="ΕΡΩΤΗΣΕΙΣ ΓΡΑΠΤΟΥ ΔΙΑΓΩΝΙΣΜΟΥ", layout="wide")

# --- ΚΕΦΑΛΙΔΑ ΕΦΑΡΜΟΓΗΣ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A; font-family: sans-serif;'>ΕΡΩΤΗΣΕΙΣ ΓΡΑΠΤΟΥ ΔΙΑΓΩΝΙΣΜΟΥ</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.warning("⚠️ Εκκρεμεί η ρύθμιση των Secrets για το Google Sheets στο Cloud. Η εφαρμογή θα λειτουργεί προσωρινά στη μνήμη.")
    conn = None

# Λίστα με τα αρχεία PDF
PDF_FILES = {
    "1. ΣΥΝΤΑΓΜΑΤΙΚΟ ΔΙΚΑΙΟ": "1.ΣΥΝΤΑΓΜΑΤΙΚΟ ΔΙΚΑΙΟ-ΛΥΣΕΙΣ.pdf",
    "2. ΔΙΟΙΚΗΤΙΚΟ ΔΙΚΑΙΟ": "2.ΔΙΟΙΚΗΤΙΚΟ ΔΙΚΑΙΟ-ΛΥΣΕΙΣ.pdf",
    "3. ΕΥΡΩΠΑΪΚΟΙ ΘΕΣΜΟΙ ΚΑΙ ΔΙΚΑΙΟ": "3.ΕΥΡΩΠΑΪΚΟΙ ΘΕΣΜΟΙ ΚΑΙ ΔΙΚΑΙΟ-ΛΥΣΕΙΣ.pdf",
    "4. ΟΙΚΟΝΟΜΙΚΕΣ ΕΠΙΣΤΗΜΕΣ": "4.ΟΙΚΟΝΟΜΙΚΕΣ ΕΠΙΣΤΗΜΕΣ-ΛΥΣΕΙΣ.pdf",
    "5. ΠΛΗΡΟΦΟΡΙΚΗ ΚΑΙ ΨΗΦΙΑΚΗ ΔΙΑΚΥΒΕΡΝΗΣΗ": "5.ΠΛΗΡΟΦΟΡΙΚΗ ΚΑΙ ΨΗΦΙΑΚΗ ΔΙΑΚΥΒΕΡΝΗΣΗ-ΛΥΣΕΙΣ.pdf",
    "6. ΣΥΓΧΡΟΝΗ ΙΣΤΟΡΙΑ ΤΗΣ ΕΛΛΑΔΟΣ": "6.ΣΥΓΧΡΟΝΗ ΙΣΤΟΡΙΑ ΤΗΣ ΕΛΛΑΔΟΣ-ΛΥΣΕΙΣ.pdf",
    "7. ΚΩΔΙΚΑΣ ΚΑΤΑΣΤΑΣΗΣ ΠΟΛΙΤΙΚΩΝ ΥΠΑΛΛΗΛΩΝ": "7.ΚΩΔΙΚΑΣ ΚΑΤΑΣΤΑΣΗΣ ΠΟΛΙΤΙΚΩΝ ΔΙΟΙΚΗΤ.ΥΠΑΛΛΗΛΩΝ ΚΑΙ ΥΠΑΛΛΗΛΩΝ ΝΠΔΔ-ΛΥΣΕΙΣ.pdf",
    "8. ΓΕΝΙΚΟΣ ΚΑΝΟΝΙΣΜΟΣ GDPR": "8.ΓΕΝΙΚΟΣ ΚΑΝΟΝΙΣΜΟΣ ΓΙΑ ΤΗΝ ΠΡΟΣΤΑΣΙΑ ΔΕΔΟΜΕΝΩΝ GDPR-ΛΥΣΕΙΣ.pdf",
    "9. ΔΙΟΙΚΗΣΗ ΕΠΙΧΕΙΡΗΣΕΩΝ ΚΑΙ ΟΡΓΑΝΙΣΜΩΝ": "9.ΔΙΟΙΚΗΣΗ ΕΠΙΧΕΙΡΗΣΕΩΝ ΚΑΙ ΟΡΓΑΝΙΣΜΩΝ-ΛΥΣΕΙΣ.pdf",
    "10. ΔΙΟΙΚΗΣΗ ΑΝΘΡΩΠΙΝΟΥ ΔΥΝΑΜΙΚΟΥ": "10.ΔΙΟΙΚΗΣΗ ΑΝΘΡΩΠΙΝΟΥ ΔΥΝΑΜΙΚΟΥ-ΛΥΣΕΙΣ.pdf",
    "11. ΚΩΔΙΚΑΣ ΣΥΜΠΕΡΙΦΟΡΑΣ ΔΗΜΟΣΙΩΝ ΥΠΑΛΛΗΛΩΝ": "11.ΚΩΔΙΚΑΣ ΣΥΜΠΕΡΙΦΟΡΑΣ ΔΗΜΟΣΙΩΝ ΥΠΑΛΛΗΛΩΝ-ΛΥΣΕΙΣ.pdf"
}

# --- ΣΥΝΑΡΤΗΣΗ ΚΑΘΑΡΙΣΜΟΥ ΚΕΙΜΕΝΟΥ ΑΠΑΝΤΗΣΕΩΝ & ΕΡΩΤΗΣΕΩΝ ---
def clean_option_text(text):
    text = re.sub(r'^[α-δΑ-Δ][\.\)]\s*', '', text)
    text = re.sub(r'(?i)Σελίδα\s*\d+\s*από\s*\d+', '', text)
    text = re.sub(r'(?i)Σελίδα\s*\d+', '', text)
    text = re.sub(r'(?i)PAGE\s*\d+', '', text)
    text = re.sub(r'(Συνταγματικό Δίκαιο|Διοικητικό Δίκαιο|Ευρωπαϊκοί Θεσμοί και Δίκαιο|Οικονομικές Επιστήμες|Πληροφορική και Ψηφιακή Διακυβέρνηση|Σύγχρονη Ιστορία της Ελλάδος|Κώδικας Κατάστασης|Γενικός Κανονισμoς|Διοίκηση επιχειρήσεων|Διοίκηση Ανθρώπινου|Κώδικας συμπεριφοράς|ΒΑΣΕΠ ΑΝΕΞΑΡΤΗΤΗ|Ανώτατο Συμβούλιο Επιλογής Προσωπικού ΑΡΧΗ|Μητρώο Θεμάτων Γνώσεων|Γνωστικό Αντικείμενο:)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(από\s*το|από|σε|του|της|στο)\b\s*$', '', text.strip(), flags=re.IGNORECASE)
    text = re.sub(r'^\s*\b(από\s*το|από|σε|του|της|στο)\b', '', text.strip(), flags=re.IGNORECASE)
    text = re.sub(r'\.{2,}', '', text) 
    return text.strip()

# --- ΜΗΧΑΝΙΣΜΟΣ PARSING PDF ---
@st.cache_data(show_spinner="Φόρτωση και ανάλυση των αρχείων PDF... Παρακαλώ περιμένετε...")
def load_all_questions():
    parsed_dataset = {}
    for section_name, file_name in PDF_FILES.items():
        parsed_dataset[section_name] = []
        if not os.path.exists(file_name):
            continue
        with pdfplumber.open(file_name) as pdf:
            current_q = None
            q_id = 1
            for page in pdf.pages:
                text_objects = page.extract_words(extra_attrs=["non_stroking_color"])
                lines = {}
                for obj in text_objects:
                    top = round(obj["top"], 1)
                    lines.setdefault(top, []).append(obj)
                for top in sorted(lines.keys()):
                    line_words = sorted(lines[top], key=lambda x: x["x0"])
                    line_text = " ".join([w["text"] for w in line_words]).strip()
                    is_red = any(w.get("non_stroking_color") and len(w["non_stroking_color"]) == 3 and w["non_stroking_color"][0] > 0.6 and w["non_stroking_color"][1] < 0.2 for w in line_words)
                    if not line_text:
                        continue
                    if line_text[0].isdigit() and ("." in line_text.split()[0] or ")" in line_text.split()[0]) and not any(line_text.startswith(prefix) for prefix in ["α.", "β.", "γ.", "δ.", "α)", "β)", "γ)", "δ)"]):
                        if current_q and len(current_q["options"]) >= 2:
                            current_q["question"] = clean_option_text(current_q["question"])
                            parsed_dataset[section_name].append(current_q)
                            q_id += 1
                        current_q = {"id": f"{section_name}_{q_id}", "question": line_text, "options": [], "correct": None, "section": section_name}
                    elif current_q and any(line_text.startswith(prefix) for prefix in ["α.", "β.", "γ.", "δ.", "α)", "β)", "γ)", "δ)"]):
                        cleaned_choice = clean_option_text(line_text)
                        if cleaned_choice and len(cleaned_choice) > 1:
                            current_q["options"].append(cleaned_choice)
                            if is_red:
                                current_q["correct"] = cleaned_choice
                    elif current_q:
                        cleaned_line = clean_option_text(line_text)
                        if cleaned_line and len(cleaned_line) > 1:
                            if current_q["options"]:
                                old_val = current_q["options"][-1]
                                updated_val = clean_option_text(old_val + " " + cleaned_line)
                                current_q["options"][-1] = updated_val
                                if is_red or current_q["correct"] == old_val:
                                    current_q["correct"] = updated_val
                            else:
                                current_q["question"] += " " + line_text
            if current_q and len(current_q["options"]) >= 2:
                current_q["question"] = clean_option_text(current_q["question"])
                parsed_dataset[section_name].append(current_q)
    return parsed_dataset

dataset = load_all_questions()

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΣΥΓΧΡΟΝΙΣΜΟΥ GOOGLE SHEETS ---
def load_progress_from_sheets():
    if conn is None:
        return {"user_answers": {}, "current_indices": {}, "submitted_sections": [], "stats": []}
    try:
        df = conn.read(ttl="0m")
        if df.empty or "key" not in df.columns:
            return {"user_answers": {}, "current_indices": {}, "submitted_sections": [], "stats": []}
        row = df.iloc[0]
        return {
            "user_answers": json.loads(row["user_answers"]) if "user_answers" in row and row["user_answers"] else {},
            "current_indices": json.loads(row["current_indices"]) if "current_indices" in row and row["current_indices"] else {},
            "submitted_sections": json.loads(row["submitted_sections"]) if "submitted_sections" in row and row["submitted_sections"] else [],
            "stats": json.loads(row["stats"]) if "stats" in row and row["stats"] else []
        }
    except:
        return {"user_answers": {}, "current_indices": {}, "submitted_sections": [], "stats": []}

def save_progress_to_sheets():
    if conn is None:
        return
    try:
        data = {
            "key": ["main_progress"],
            "user_answers": [json.dumps(st.session_state.user_answers, ensure_ascii=False)],
            "current_indices": [json.dumps(st.session_state.current_indices, ensure_ascii=False)],
            "submitted_sections": [json.dumps(list(st.session_state.submitted_sections), ensure_ascii=False)],
            "stats": [json.dumps(st.session_state.stats, ensure_ascii=False)]
        }
        df = pd.DataFrame(data)
        conn.update(data=df)
    except:
        pass

# Φόρτωση δεδομένων κατά την εκκίνηση
if "data_loaded" not in st.session_state:
    saved_data = load_progress_from_sheets()
    st.session_state.user_answers = saved_data["user_answers"]
    initial_indices = {k: 0 for k in dataset.keys()}
    initial_indices["🎲 ΤΥΧΑΙΟ ΤΕΣΤ (30 ΕΡΩΤΗΣΕΙΣ)"] = 0
    for k, v in saved_data["current_indices"].items():
        initial_indices[k] = v
    st.session_state.current_indices = initial_indices
    st.session_state.submitted_sections = set(saved_data["submitted_sections"])
    st.session_state.stats = saved_data["stats"]
    st.session_state.data_loaded = True

if "random_test_questions" not in st.session_state:
    st.session_state.random_test_questions = []
if "active_mode" not in st.session_state:
    st.session_state.active_mode = "regular"  
if "shuffled_options" not in st.session_state:
    st.session_state.shuffled_options = {}
if "timer_start" not in st.session_state:
    st.session_state.timer_start = None
if "show_preview" not in st.session_state:
    st.session_state.show_preview = False
if "last_selected_section" not in st.session_state:
    st.session_state.last_selected_section = None
if "last_use_timer" not in st.session_state:
    st.session_state.last_use_timer = False

def get_shuffled_options(question):
    q_id = question["id"]
    if q_id not in st.session_state.shuffled_options:
        st.session_state.shuffled_options[q_id] = random.sample(question["options"], len(question["options"]))
    return st.session_state.shuffled_options[q_id]

def generate_random_test():
    all_questions = []
    for sec_qs in dataset.values():
        all_questions.extend(sec_qs)
    sample_size = min(30, len(all_questions))
    st.session_state.random_test_questions = random.sample(all_questions, sample_size)
    st.session_state.current_indices["🎲 ΤΥΧΑΙΟ ΤΕΣΤ (30 ΕΡΩΤΗΣΕΙΣ)"] = 0
    st.session_state.user_answers["🎲 ΤΥΧΑΙΟ ΤΕΣΤ (30 ΕΡΩΤΗΣΕΙΣ)"] = {q["id"]: None for q in st.session_state.random_test_questions}
    for q in st.session_state.random_test_questions:
        if q["id"] in st.session_state.shuffled_options:
            del st.session_state.shuffled_options[q["id"]]
    if "🎲 ΤΥΧΑΙΟ ΤΕΣΤ (30 ΕΡΩΤΗΣΕΙΣ)" in st.session_state.submitted_sections:
        st.session_state.submitted_sections.remove("🎲 ΤΥΧΑΙOR ΤΕΣΤ (30 ΕΡΩΤΗΣΕΙΣ)")
    st.session_state.show_preview = False
    st.session_state.timer_start = None  
    save_progress_to_sheets()

# --- ΣΥΝΑΡΤΗΣΗ ΕΛΕΓΧΟΥ: ΥΠΑΡΧΟΥΝ ΛΑΘΗ ΣΤΗ ΜΝΗΜΗ; ---
def check_if_any_errors_exist():
    """Επιστρέφει True αν ο χρήστης έχει απαντήσει έστω και μία ερώτηση λάθος."""
    for sec_name, questions_list in dataset.items():
        ans_dict = st.session_state.user_answers.get(sec_name, {})
        for q_item in questions_list:
            u_ans = ans_dict.get(q_item["id"], None)
            if u_ans is not None and u_ans != q_item["correct"]:
                return True
                
    random_answers_dict = st.session_state.user_answers.get("🎲 ΤΥΧΑΙΟ ΤΕΣΤ (30 ΕΡΩΤΗΣΕΙΣ)", {})
    for q_item in st.session_state.random_test_questions:
        u_ans = random_answers_dict.get(q_item["id"], None)
        if u_ans is not None and u_ans != q_item["correct"]:
            return True
            
    return False

# --- ΣΥΝΑΡΤΗΣΗ ΔΗΜΙΟΥΡΓΙΑΣ EXCEL ΜΕ ΚΑΡΤΕΛΕΣ ---
def export_all_errors_to_excel():
    """Σαρώνει όλες τις απαντήσεις και παράγει ένα Excel με tabs για κάθε ενότητα."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sec_name, questions_list in dataset.items():
            wrong_data = []
            for q_item in questions_list:
                u_ans = st.session_state.user_answers.get(sec_name, {}).get(q_item["id"], None)
                if u_ans is not None and u_ans != q_item["correct"]:
                    wrong_data.append({
                        "Ερώτηση": q_item["question"],
                        "Η Απάντησή σας": u_ans if u_ans else "❌ Δεν απαντήθηκε",
                        "Σωστή Απάντηση": q_item["correct"] if q_item["correct"] else "Δεν ανιχνεύθηκε"
                    })
            if wrong_data:
                df = pd.DataFrame(wrong_data)
                clean_tab_name = re.sub(r'[\\/*?:\[\]]', '', sec_name)[:30]
                df.to_excel(writer, sheet_name=clean_tab_name, index=False)
                    
        random_answers_dict = st.session_state.user_answers.get("🎲 ΤΥΧΑΙΟ ΤΕΣΤ (30 ΕΡΩΤΗΣΕΙΣ)", {})
        if random_answers_dict:
            random_wrong = []
            for q_item in st.session_state.random_test_questions:
                u_ans = random_answers_dict.get(q_item["id"], None)
                if u_ans is not None and u_ans != q_item["correct"]:
                    random_wrong.append({
                        "Ενότητα Προέλευσης": q_item["section"],
                        "Ερώτηση": q_item["question"],
                        "Η Απάντησή σας": u_ans if u_ans else "❌ Δεν απαντήθηκε",
                        "Σωστή Απάντηση": q_item["correct"]
                    })
            if random_wrong:
                df_rand = pd.DataFrame(random_wrong)
                df_rand.to_excel(writer, sheet_name="ΤΥΧΑΙΟ ΤΕΣΤ", index=False)
            
    return output.getvalue()


# --- ΑΡΙΣΤΕΡΟ ΜΕΡΟΣ: Sidebar (Μενού) ---
st.sidebar.header("📁 Ενότητες")
selected_section_box = st.sidebar.selectbox("Επιλέξτε Ενότητα για απάντηση:", options=list(dataset.keys()), disabled=(st.session_state.active_mode == "random_test"))
st.sidebar.markdown("---")

# ΔΥΝΑΜΙΚΗ ΕΜΦΑΝΙΣΗ ΚΟΥΜΠΙΟΥ EXCEL ΜΟΝΟ ΑΝ ΥΠΑΡΧΕΙ ΕΣΤΩ ΚΑΙ ΜΙΑ ΛΑΘΟΣ ΑΠΑΝΤΗΣΗ
if check_if_any_errors_exist():
    st.sidebar.subheader("📥 Λήψη Δεδομένων")
    excel_file_bytes = export_all_errors_to_excel()
    st.sidebar.download_button(
        label="📥 Εξαγωγή Λαθών σε Excel",
        data=excel_file_bytes,
        file_name="wrong_questions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch"
    )
    st.sidebar.markdown("---")

if st.session_state.last_selected_section != selected_section_box:
    st.session_state.timer_start = None
    st.session_state.last_selected_section = selected_section_box

current_active_section = "🎲 ΤΥΧΑΙΟ ΤΕΣΤ (30 ΕΡΩΤΗΣΕΙΣ)" if st.session_state.active_mode == "random_test" else selected_section_box

if st.session_state.active_mode == "regular":
    if st.sidebar.button("🎲 Έναρξη Τυχαίου Τεστ (30 ερωτήσεις)", width="stretch", type="primary"):
        generate_random_test()
        st.session_state.active_mode = "random_test"
        st.rerun()
else:
    if st.sidebar.button("🔄 Παραγωγή Νέου Τυχαίου Τεστ", width="stretch"):
        generate_random_test()
        st.rerun()
    if st.sidebar.button("⬅️ Επιστροφή στις Ενότητες", width="stretch", type="secondary"):
        st.session_state.active_mode = "regular"
        st.session_state.show_preview = False
        st.session_state.timer_start = None  
        st.rerun()

if st.sidebar.button("🔄 Έναρξη Τεστ από την Αρχή", width="stretch", type="secondary"):
    st.session_state.timer_start = None  
    st.session_state.current_indices[current_active_section] = 0  
    st.session_state.show_preview = False
    if current_active_section in st.session_state.submitted_sections:
        st.session_state.submitted_sections.remove(current_active_section)
    if current_active_section == "🎲 ΤΥΧΑΙΟ ΤΕΣΤ (30 ΕΡΩΤΗΣΕΙΣ)":
        st.session_state.user_answers[current_active_section] = {q["id"]: None for q in st.session_state.random_test_questions}
    else:
        st.session_state.user_answers[current_active_section] = {q["id"]: None for q in dataset[current_active_section]}
    save_progress_to_sheets()  
    st.rerun()

# --- ΠΑΝΩ ΜΕΡΟΣ: ΡΥΘΜΙΣΗ ΡΟΛΟΓΙΟΥ & ΣΤΑΤΙΣΤΙΚΩΝ ---
col_timer_switch, col_timer_duration, col_timer_display, col_stats = st.columns([1.5, 1.5, 1.5, 1.5])
with col_timer_switch:
    use_timer = st.toggle("⏱️ Ενεργοποίηση Χρονόμετρου", key="timer_toggle_widget")
    if st.session_state.last_use_timer != use_timer:
        if not use_timer:
            st.session_state.timer_start = None
        st.session_state.last_use_timer = use_timer

with col_timer_duration:
    if use_timer:
        timer_duration_minutes = st.selectbox("Διάρκεια:", options=[30, 60, 90], format_func=lambda x: f"{x} λεπτά (1,5 ώρα)" if x == 90 else f"{x} λεπτά")
    else:
        st.write("")

with col_timer_display:
    if use_timer:
        if st.session_state.timer_start is None:
            if st.button("⏱️ Έναρξη Χρόνου", width="stretch"):
                st.session_state.timer_start = time.time()
                st.rerun()
        else:
            elapsed = time.time() - st.session_state.timer_start
            remaining = (timer_duration_minutes * 60) - elapsed
            if remaining <= 0:
                st.error("🚨 Τέλος Χρόνου!")
                st.session_state.submitted_sections.add(current_active_section)
                st.session_state.timer_start = None
                save_progress_to_sheets()
            else:
                mins, secs = divmod(int(remaining), 60)
                st.metric(label="Υπολειπόμενος Χρόνος", value=f"{mins:02d}:{secs:02d}")
    else:
        st.write("")

with col_stats:
    show_stats = st.button("📊 Προβολή Στατιστικών", width="stretch")

if show_stats:
    st.markdown("### 📈 Ιστορικό Προσπαθειών")
    if not st.session_state.stats:
        st.info("Δεν υπάρχουν ακόμη καταγεγραμμένες ολοκληρωμένες προσπάθειες.")
    else:
        df_stats = pd.DataFrame(st.session_state.stats)
        st.dataframe(df_stats, width="stretch", hide_index=True)
    st.markdown("---")

if st.session_state.active_mode == "random_test":
    selected_section = "🎲 ΤΥΧΑΙΟ ΤΕΣΤ (30 ΕΡΩΤΗΣΕΙΣ)"
    questions = st.session_state.random_test_questions
else:
    selected_section = selected_section_box
    questions = dataset[selected_section]

if not questions:
    st.warning(f"⚠️ Δεν βρέθηκαν ερωτήσεις για την επιλογή: '{selected_section}'.")
else:
    if selected_section not in st.session_state.user_answers:
        st.session_state.user_answers[selected_section] = {q["id"]: None for q in questions}

    current_idx = st.session_state.current_indices.get(selected_section, 0)
    if current_idx >= len(questions):
        current_idx = len(questions) - 1
        st.session_state.current_indices[selected_section] = current_idx

    # --- ΣΥΓΧΡΟΝΙΣΜΕΝΗ ΜΕΤΑΒΑΣΗ ΜΕ CALLBACK FUNCTION ---
    def handle_jump_callback():
        requested_page = st.session_state[f"jump_input_{selected_section}"]
        st.session_state.current_indices[selected_section] = requested_page - 1
        save_progress_to_sheets()

    col_title_text, col_jump_input = st.columns([3, 1])
    
    with col_title_text:
        st.markdown(f"### 📍 {selected_section}")
        
    with col_jump_input:
        st.number_input(
            "Μετάβαση σε ερώτηση:",
            min_value=1,
            max_value=len(questions),
            value=current_idx + 1,
            step=1,
            key=f"jump_input_{selected_section}",
            on_change=handle_jump_callback
        )

    current_q = questions[current_idx]
    st.write(f"**Ερώτηση {current_idx + 1} από {len(questions)}**")
    st.info(f"**{current_q['question']}**")
    
    current_saved_ans = st.session_state.user_answers[selected_section].get(current_q["id"], None)
    shuffled_choices = get_shuffled_options(current_q)
    
    default_idx = None
    if current_saved_ans in shuffled_choices:
        default_idx = shuffled_choices.index(current_saved_ans)
        
    selected_option = st.radio("Επιλέξτε την ορθή απάντηση:", options=shuffled_choices, index=default_idx, key=f"radio_{selected_section}_{current_q['id']}")
    
    if selected_option and selected_option != current_saved_ans:
        st.session_state.user_answers[selected_section][current_q["id"]] = selected_option
        save_progress_to_sheets()

    # --- ΠΛΟΗΓΗΣΗ (ΒΕΛΑΚΙΑ) ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_prev, col_submit, col_next = st.columns([1, 2, 1])
    with col_prev:
        if current_idx > 0:
            if st.button("⬅️  Προηγούμενη", width="stretch"):
                st.session_state.current_indices[selected_section] -= 1
                save_progress_to_sheets()
                st.rerun()
    with col_next:
        if current_idx < len(questions) - 1:
            if st.button("Επόμενη ➡️", width="stretch"):
                st.session_state.current_indices[selected_section] += 1
                save_progress_to_sheets()
                st.rerun()

    # --- ΚΟΥΜΠΙ ΠΡΟΩΡΗΣ ΕΠΙΣΚΟΠΗΣΗΣ ΚΑΘΕ 30 ΕΡΩΤΗΣΕΙΣ ---
    is_checkpoint = (current_idx + 1) % 30 == 0
    if is_checkpoint and selected_section not in st.session_state.submitted_sections:
        st.markdown("---")
        col_space1, col_preview_btn, col_space2 = st.columns([1, 2, 1])
        with col_preview_btn:
            if st.button("👁️ Πρόωρη Επισκόπηση Αποτελεσμάτων (Μέχρι Τώρα)", width="stretch"):
                st.session_state.show_preview = not st.session_state.show_preview

        if st.session_state.show_preview:
            st.markdown("#### 📊 Στατιστικά Τρέχουσας Προόδου (Μέχρι την ερώτηση {})".format(current_idx + 1))
            preview_correct = 0
            preview_wrong_data = []
            for i in range(current_idx + 1):
                q_item = questions[i]
                u_ans = st.session_state.user_answers[selected_section].get(q_item["id"], None)
                if u_ans and u_ans == q_item["correct"]:
                    preview_correct += 1
                else:
                    preview_wrong_data.append({"Ερώτηση": i + 1, "Περιεχόμενο": q_item["question"], "Σωστή Απάντηση": q_item["correct"], "Η Απάντησή σας": u_ans if u_ans else "❌ Δεν απαντήθηκε"})
            st.write(f"Σωστά: **{preview_correct}** | Λάθη/Αναπάντητα: **{(current_idx + 1) - preview_correct}**")
            if preview_wrong_data:
                st.dataframe(pd.DataFrame(preview_wrong_data), width="stretch", hide_index=True)

    # --- ΥΠΟΒΟΛΗ ΚΑΙ ΤΕΛΙΚΑ ΑΠΟΤΕΛΕΣΜΑΤΑ ---
    is_last_question = current_idx == len(questions) - 1
    if is_last_question and selected_section not in st.session_state.submitted_sections:
        with col_submit:
            if st.button("Ολοκλήρωση & Υποβολή Ενότητας", type="primary", width="stretch"):
                st.session_state.submitted_sections.add(selected_section)
                st.session_state.timer_start = None  
                save_progress_to_sheets()
                st.rerun()

    if selected_section in st.session_state.submitted_sections:
        st.markdown("---")
        st.markdown("### 📊 Αποτελέσματα Ενότητας")
        st.markdown("<br>", unsafe_allow_html=True)
        
        correct_count = 0
        wrong_questions_data = []
        for q in questions:
            user_ans = st.session_state.user_answers[selected_section].get(q["id"], None)
            if user_ans and user_ans == q["correct"]:
                correct_count += 1
            else:
                wrong_questions_data.append({
                    "Προέλευση": q["section"], 
                    "Ερώτηση": q["question"], 
                    "Σωστή Απάντηση": q["correct"] if q["correct"] else "Δεν ανιχνεύθηκε", 
                    "Η Απάντησή σας": user_ans if user_ans else "❌ Δεν απαντήθηκε (Λάθος)"
                })
        st.success(f"Απαντήσατε σωστά σε **{correct_count}** από τις **{len(questions)}** ερωτήσεις.")
        stats_entry = {"Ενότητα": selected_section, "Σωστά": correct_count, "Σύνολο": len(questions), "Ποσοστό": f"{(correct_count/len(questions))*100:.1f}%"}
        if stats_entry not in st.session_state.stats:
            st.session_state.stats.append(stats_entry)
            save_progress_to_sheets()

        if wrong_questions_data:
            st.markdown("#### ❌ Πίνακας Λανθασμένων / Αναπάντητων Ερωτήσεων")
            df_wrong = pd.DataFrame(wrong_questions_data)
            st.dataframe(df_wrong, width="stretch", hide_index=True)
        else:
            st.success("🎉 Εξαιρετικά! 100% Επιτυχία!")
            
        if st.button("🔄 Επανάληψη Ενότητας", width="stretch"):
            st.session_state.submitted_sections.remove(selected_section)
            st.session_state.current_indices[selected_section] = 0
            st.session_state.show_preview = False
            st.session_state.timer_start = None  
            if selected_section == "🎲 ΤΥΧΑΙΟ ΤΕΣΤ (30 ΕΡΩΤΗΣΕΙΣ)":
                for q in st.session_state.random_test_questions:
                    if q["id"] in st.session_state.shuffled_options:
                        del st.session_state.shuffled_options[q["id"]]
                st.session_state.user_answers[selected_section] = {q["id"]: None for q in st.session_state.random_test_questions}
            else:
                for q in questions:
                    if q["id"] in st.session_state.shuffled_options:
                        del st.session_state.shuffled_options[q["id"]]
                st.session_state.user_answers[selected_section] = {q["id"]: None for q in questions}
            save_progress_to_sheets()
            st.rerun()

if use_timer and st.session_state.timer_start is not None:
    time.sleep(1)
    st.rerun()
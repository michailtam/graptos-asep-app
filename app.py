import streamlit as st
import pandas as pd
import pdfplumber
import os
import random
import re

# --- ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="ΕΡΩΤΗΣΕΙΣ ΓΡΑΠΤΟΥ ΔΙΑΓΩΝΙΣΜΟΥ", layout="wide")

# --- ΚΕΦΑΛΙΔΑ ΕΦΑΡΜΟΓΗΣ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A; font-family: sans-serif;'>ΕΡΩΤΗΣΕΙΣ ΓΡΑΠΤΟΥ ΔΙΑΓΩΝΙΣΜΟΥ</h1>", unsafe_allow_html=True)
st.markdown("---")

# Λίστα με τα ακριβή ονόματα των 11 αρχείων PDF σας
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

# Βοηθητική συνάρτηση για τον καθαρισμό των γραμμάτων α., β., γ., δ. από τις απαντήσεις
def clean_option_text(text):
    return re.sub(r'^[α-δΑ-Δ][\.\)]\s*', '', text).strip()

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
                    
                    is_red = any(
                        w.get("non_stroking_color") and 
                        len(w["non_stroking_color"]) == 3 and 
                        w["non_stroking_color"][0] > 0.6 and w["non_stroking_color"][1] < 0.2 
                        for w in line_words
                    )
                    
                    if not line_text:
                        continue
                        
                    if line_text[0].isdigit() and ("." in line_text.split()[0] or ")" in line_text.split()[0]) and not any(line_text.startswith(prefix) for prefix in ["α.", "β.", "γ.", "δ.", "α)", "β)", "γ)", "δ)"]):
                        if current_q and len(current_q["options"]) >= 2:
                            parsed_dataset[section_name].append(current_q)
                            q_id += 1
                        
                        current_q = {
                            "id": f"{section_name}_{q_id}",
                            "question": line_text,
                            "options": [],
                            "correct": None,
                            "section": section_name
                        }
                    
                    elif current_q and any(line_text.startswith(prefix) for prefix in ["α.", "β.", "γ.", "δ.", "α)", "β)", "γ)", "δ)"]):
                        cleaned_choice = clean_option_text(line_text)
                        current_q["options"].append(cleaned_choice)
                        if is_red:
                            current_q["correct"] = cleaned_choice
                            
                    elif current_q and not current_q["options"]:
                        current_q["question"] += " " + line_text
            
            if current_q and len(current_q["options"]) >= 2:
                parsed_dataset[section_name].append(current_q)
                
    return parsed_dataset

# Φόρτωση δεδομένων
dataset = load_all_questions()

# --- ΑΡΧΙΚΟΠΟΙΗΣΗ SESSION STATES ---
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}  
if "current_indices" not in st.session_state:
    st.session_state.current_indices = {k: 0 for k in dataset.keys()}
    st.session_state.current_indices["🎲 ΤΥΧΑΙΟ ΤΕΣΤ (30 ΕΡΩΤΗΣΕΙΣ)"] = 0
if "submitted_sections" not in st.session_state:
    st.session_state.submitted_sections = set()
if "stats" not in st.session_state:
    st.session_state.stats = []  
if "random_test_questions" not in st.session_state:
    st.session_state.random_test_questions = []
if "active_mode" not in st.session_state:
    st.session_state.active_mode = "regular"  
if "shuffled_options" not in st.session_state:
    st.session_state.shuffled_options = {}

# --- ΣΥΝΑΡΤΗΣΗ ΓΙΑ ΑΝΑΚΑΤΕΜΑ ΕΠΙΛΟΓΩΝ ---
def get_shuffled_options(question):
    q_id = question["id"]
    if q_id not in st.session_state.shuffled_options:
        st.session_state.shuffled_options[q_id] = random.sample(question["options"], len(question["options"]))
    return st.session_state.shuffled_options[q_id]

# --- ΔΗΜΟΥΡΓΙΑ ΤΥΧΑΙΟΥ ΤΕΣΤ ---
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
        st.session_state.submitted_sections.remove("🎲 ΤΥΧΑΙΟ ΤΕΣΤ (30 ΕΡΩΤΗΣΕΙΣ)")

# --- ΚΟΥΜΠΙ ΣΤΑΤΙΣΤΙΚΩΝ (Πάνω Δεξιά) ---
col_title, col_stats = st.columns([4, 1])
with col_stats:
    show_stats = st.button("📊 Προβολή Στατιστικών", use_container_width=True)

if show_stats:
    st.markdown("### 📈 Ιστορικό Προσπαθειών")
    if not st.session_state.stats:
        st.info("Δεν υπάρχουν ακόμη καταγεγραμμένες ολοκληρωμένες προσπάθειες.")
    else:
        df_stats = pd.DataFrame(st.session_state.stats)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)
    st.markdown("---")

# --- ΑΡΙΣΤΕΡΟ ΜΕΡΟΣ: Sidebar (Μενού) ---
st.sidebar.header("📁 Ενότητες")

# Η λίστα περιλαμβάνει ΜΟΝΟ τις 11 κανονικές ενότητες (Το Τυχαίο Τεστ αφαιρέθηκε)
selected_section_box = st.sidebar.selectbox(
    "Επιλέξτε Ενότητα για απάντηση:",
    options=list(dataset.keys()),
    disabled=(st.session_state.active_mode == "random_test")
)

st.sidebar.markdown("---")

# --- ΚΟΥΜΠΙ ΤΥΧΑΙΟΥ ΤΕΣΤ ΣΤΟ ΚΑΤΩ ΜΕΡΟΣ ΤΟΥ ΜΕΝΟΥ ---
if st.session_state.active_mode == "regular":
    if st.sidebar.button("🎲 Έναρξη Τυχαίου Τεστ (30 ερωτήσεις)", use_container_width=True, type="primary"):
        generate_random_test()
        st.session_state.active_mode = "random_test"
        st.rerun()
else:
    if st.sidebar.button("🔄 Παραγωγή Νέου Τυχαίου Τεστ", use_container_width=True):
        generate_random_test()
        st.rerun()
    if st.sidebar.button("⬅️ Επιστροφή στις Ενότητες", use_container_width=True, type="secondary"):
        st.session_state.active_mode = "regular"
        st.rerun()

# Καθορισμός ενεργής ενότητας
if st.session_state.active_mode == "random_test":
    selected_section = "🎲 ΤΥΧΑΙΟ ΤΕΣΤ (30 ΕΡΩΤΗΣΕΙΣ)"
    questions = st.session_state.random_test_questions
else:
    selected_section = selected_section_box
    questions = dataset[selected_section]

# Έλεγχος αν βρέθηκαν ερωτήσεις
if not questions:
    st.warning(f"⚠️ Δεν βρέθηκαν ερωτήσεις για την επιλογή: '{selected_section}'.")
else:
    if selected_section not in st.session_state.user_answers:
        st.session_state.user_answers[selected_section] = {q["id"]: None for q in questions}

    current_idx = st.session_state.current_indices[selected_section]
    current_q = questions[current_idx]
    
    st.markdown(f"### 📍 {selected_section} (Ερώτηση {current_idx + 1} από {len(questions)})")
    
    # --- ΚΕΝΤΡΙΚΟ ΜΕΡΟΣ ---
    st.info(f"**{current_q['question']}**")
    
    current_saved_ans = st.session_state.user_answers[selected_section][current_q["id"]]
    shuffled_choices = get_shuffled_options(current_q)
    
    default_idx = None
    if current_saved_ans in shuffled_choices:
        default_idx = shuffled_choices.index(current_saved_ans)
        
    selected_option = st.radio(
        "Επιλέξτε την ορθή απάντηση:",
        options=shuffled_choices,
        index=default_idx,
        key=f"radio_{selected_section}_{current_q['id']}"
    )
    
    if selected_option:
        st.session_state.user_answers[selected_section][current_q["id"]] = selected_option

    # --- ΠΛΟΗΓΗΣΗ (Βελάκια) ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_prev, col_submit, col_next = st.columns([1, 2, 1])
    
    with col_prev:
        if current_idx > 0:
            if st.button("⬅️ Προηγούμενη", use_container_width=True):
                # Καθαρισμός απάντησης της ερώτησης από την οποία πλοηγούμαστε προς τα πίσω
                st.session_state.user_answers[selected_section][current_q["id"]] = None
                st.session_state.current_indices[selected_section] -= 1
                st.rerun()
                
    with col_next:
        if current_idx < len(questions) - 1:
            if st.button("Επόμενη ➡️", use_container_width=True):
                st.session_state.current_indices[selected_section] += 1
                st.rerun()

# --- ΥΠΟΒΟΛΗ ΚΑΙ ΑΠΟΤΕΛΕΣΜΑΤΑ ---
    is_last_question = current_idx == len(questions) - 1
    
    if is_last_question and selected_section not in st.session_state.submitted_sections:
        with col_submit:
            if st.button("🏁 Ολοκλήρωση & Υποβολή Ενότητας", type="primary", use_container_width=True):
                st.session_state.submitted_sections.add(selected_section)
                st.rerun()

    if selected_section in st.session_state.submitted_sections:
        st.markdown("---")
        st.markdown("### 📊 Αποτελέσματα Ενότητας")
        
        correct_count = 0
        wrong_questions_data = []
        
        for q in questions:
            user_ans = st.session_state.user_answers[selected_section][q["id"]]
            
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

        if wrong_questions_data:
            st.markdown("#### ❌ Πίνακας Λανθασμένων / Αναπάντητων Ερωτήσεων")
            df_wrong = pd.DataFrame(wrong_questions_data)
            st.dataframe(df_wrong, use_container_width=True, hide_index=True)
        else:
            st.balloons()
            st.success("🎉 Εξαιρετικά! 100% Επιτυχία!")
            
        if st.button("🔄 Επανάληψη Ενότητας"):
            st.session_state.submitted_sections.remove(selected_section)
            st.session_state.current_indices[selected_section] = 0
            
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
            st.rerun()
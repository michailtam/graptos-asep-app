# Test Preparation Application for the Greek ASEP (Supreme Council for Civil Personnel Selection)
A lightweight, AI-assisted Python web application designed to help users efficiently practice and prepare for the **ASEP (Supreme Council for Civil Personnel Selection)** exams. 
By leveraging cloud deployment, this app seamlessly processes an extensive database of 2,000 questions without draining local device resources, making it perfect for both desktop and mobile use.

## Features
* **Language Support** The user interface is exclusively in Greek to natively align with the official Greek ASEP exam material.
* **AI-Optimized:** Built with the assistance of AI to ensure fast development, clean logic, and efficient test-taking workflows.
* **Cross-Platform Compatibility:** Runs perfectly in your local environment or on mobile devices (successfully tested on **iPhone 12 Pro**).
* **Cloud-Powered Performance:** Deployed via Streamlit Cloud to handle heavy data processing (parsing 2,000+ questions) seamlessly, ensuring your mobile device doesn't overheat or slow down.
* **Smart Data Parsing:** Extracts and organizes exam content from complex PDF sources effortlessly.
* **Stopwatch:** Switch button to turn the timer on or off and to set it.
* **Random Test:** Option to execute a random test.
* **Export to Excel** Option to export all wrong answers by section as an excel file.

## Getting Started
Ensure you have Python installed on your system. You will also need to install the required dependencies:

```bash
pip install streamlit pandas pdfplumber openpyxl (for online usage: the libraries streamlit-local-storage and st-gsheets-connection are also needed).
python -m streamlit run app.py
```

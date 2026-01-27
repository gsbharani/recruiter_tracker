import re
import pdfplumber

def extract_text(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "

    return clean_text(text)

def extract_skills(text):
    skills = [
        "python", "sql", "excel", "aws", "docker",
        "pandas", "numpy", "machine learning",
        "streamlit", "postgres", "supabase"
    ]
    return {skill for skill in skills if skill in text}
def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text

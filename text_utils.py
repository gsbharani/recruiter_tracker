import re
import pdfplumber

def extract_text_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.lower()

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

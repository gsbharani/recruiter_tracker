import re
import pdfplumber
import streamlit as st

# ---------------- Text extraction ----------------
def extract_text(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
    return clean_text(text)

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text

# ---------------- Skill Matching ----------------
def match_skills(resume_text: str, required_skills: list) -> tuple[list, list]:
    """
    Returns two lists: matched_skills, missing_skills
    """
    resume_text_lower = resume_text.lower()
    matched = []
    missing = []

    for skill in required_skills:
        if skill.lower() in resume_text_lower:
            matched.append(skill)
        else:
            missing.append(skill)

    return matched, missing

# ---------------- Streamlit UI ----------------
skills_input = st.text_input(
    "Enter required skills (comma separated)",
    placeholder="Python, SQL, Excel, AWS"
)

if skills_input:
    required_skills = [s.strip() for s in skills_input.split(",") if s.strip()]
    
    # Suppose resume_text is already extracted
    # resume_text = extract_text(uploaded_resume_path)
    # For demo:
    resume_text = "Python, SQL, data analysis, excel"
    
    matched, missing = match_skills(resume_text, required_skills)
    st.success(f"✅ Matched Skills: {matched}")
    st.error(f"❌ Missing Skills: {missing}")

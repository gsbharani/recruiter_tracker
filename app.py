import streamlit as st
import tempfile
import uuid

from supabase_client import supabase
from resume_utils import extract_text_from_pdf, extract_skills
from matcher import match_resume_to_jd

st.set_page_config("Recruiter JD Matcher", layout="wide")
st.title("📄 Resume ↔ JD Matcher")

# ---- Recruiter ----
st.subheader("Recruiter")
recruiter_id = st.text_input("Recruiter UUID")

# ---- JD Upload ----
st.subheader("Upload Job Description (PDF)")
jd_file = st.file_uploader("JD PDF", type=["pdf"], key="jd")

if jd_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(jd_file.read())
        jd_text = extract_text_from_pdf(tmp.name)
        jd_skills = extract_skills(jd_text)

    st.success(f"JD Skills: {', '.join(jd_skills)}")

# ---- Resume Upload ----
st.subheader("Upload Resume")
resume_file = st.file_uploader("Resume PDF", type=["pdf"], key="resume")

if resume_file and jd_file and recruiter_id:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(resume_file.read())
        resume_text = extract_text_from_pdf(tmp.name)
        resume_skills = extract_skills(resume_text)

    result = match_resume_to_jd(resume_skills, jd_skills)

    supabase.table("candidates").insert({
        "id": str(uuid.uuid4()),
        "recruiter_id": recruiter_id,
        "resume_url": resume_file.name,
        "score": result["score"],
        "matched_skills": result["matched"],
        "missing_skills": result["missing"]
    }).execute()

    st.success(f"Match Score: {result['score']}%")
    st.write("✅ Matched Skills:", result["matched"])
    st.write("❌ Missing Skills:", result["missing"])

import streamlit as st
import tempfile
import uuid
import pandas as pd

from resume_parser import parse_resume
from text_utils import extract_text
from matcher import semantic_score, skill_score
from supabase_client import supabase

st.set_page_config("Recruiter JD Matcher", layout="wide")
st.title("🧑‍💼✅ Find the Best-Fit Candidates for Your Job — Instantly")

# ---------------- Recruiter ----------------
st.header("Recruiter")
recruiter_name = st.text_input("Your Name")

if st.button("Create / Load Recruiter"):
    res = supabase.table("recruiters").select("*").eq("name", recruiter_name).execute()

    if res.data:
        recruiter_id = res.data[0]["id"]
    else:
        recruiter = supabase.table("recruiters").insert({
            "name": recruiter_name
        }).execute()
        recruiter_id = recruiter.data[0]["id"]

    st.session_state["recruiter_id"] = recruiter_id
    st.success(f"Recruiter ready: {recruiter_id}")

if "recruiter_id" not in st.session_state:
    st.stop()

# ---------------- JD Upload ----------------
st.header("Job Description")
jd_file = st.file_uploader("Upload JD (PDF)", type=["pdf"])

if jd_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(jd_file.read())
        st.session_state["jd_text"] = extract_text(tmp.name)

    st.success("JD uploaded")

if "jd_text" not in st.session_state:
    st.stop()

# ---------------- Skills ----------------
st.subheader("Required Skills")
skills_input = st.text_input("Enter skills (comma separated)", placeholder="Python, SQL, AWS")

if skills_input:
    st.session_state["skills"] = [s.strip().lower() for s in skills_input.split(",")]
    st.success(f"Skills added: {skills_input}")

# ---------------- Resume Upload ----------------
st.header("Upload Resumes")
resume_files = st.file_uploader(
    "Upload Resume (PDF/DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

results = []

if "uploaded_resumes" not in st.session_state:
    st.session_state["uploaded_resumes"] = set()

if resume_files:
    for resume_file in resume_files:
        if resume_file.name in st.session_state["uploaded_resumes"]:
            continue

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(resume_file.read())
            resume_path = tmp.name

        resume_text = extract_text(resume_path)
        parsed = parse_resume(resume_path, st.session_state.get("skills", []))

        jd_score = semantic_score(st.session_state["jd_text"], resume_text)
        skill_match = skill_score(resume_text, st.session_state.get("skills", []))
        final_score = round((jd_score * 0.7) + (skill_match * 0.3), 2)

        supabase.table("candidates").insert({
            "id": str(uuid.uuid4()),
            "recruiter_id": st.session_state["recruiter_id"],
            "resume_name": resume_file.name,
            "email": parsed["email"],
            "phone": parsed["phone"],
            "experience": parsed["experience"],
            "score": final_score,
            "skills": parsed["skills_found"]
        }).execute()

        st.session_state["uploaded_resumes"].add(resume_file.name)

        results.append({
            "Resume": resume_file.name,
            "Fit %": final_score
        })

        st.markdown(f"""
        **📄 {resume_file.name}**
        - 🧠 JD Match: **{jd_score}%**
        - 🛠 Skill Match: **{skill_match}%**
        - 🎯 Final Score: **{final_score}%**
        """)

# ---------------- Ranking ----------------
st.header("📊 Ranked Candidates")

db_results = supabase.table("candidates") \
    .select("resume_name, score") \
    .eq("recruiter_id", st.session_state["recruiter_id"]) \
    .order("score", desc=True) \
    .execute()

if not db_results.data:
    st.info("No candidates uploaded yet.")
    st.stop()

df = pd.DataFrame(db_results.data)
st.dataframe(df)

df["shortlist"] = df["score"] >= 70
shortlisted = df[df["shortlist"]]

st.download_button(
    "Download Shortlisted (CSV)",
    shortlisted.to_csv(index=False),
    file_name="shortlisted_resumes.csv"
)

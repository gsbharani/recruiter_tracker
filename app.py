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
    st.success(f"Recruiter ready")

if "recruiter_id" not in st.session_state:
    st.stop()

# ---------------- Load Existing JDs ----------------
st.subheader("Your Saved Job Descriptions")

jds = supabase.table("job_requirements") \
    .select("id, title, jd_text, skills") \
    .eq("client_id", st.session_state["recruiter_id"]) \
    .execute()

jd_map = {jd["title"]: jd for jd in jds.data}

selected_jd = st.selectbox(
    "Select JD",
    ["Create New JD"] + list(jd_map.keys())
)

if selected_jd != "Create New JD":
    jd = jd_map[selected_jd]
    st.session_state["jd_text"] = jd["jd_text"]
    st.session_state["skills"] = jd["skills"]
    st.session_state["jd_id"] = jd["id"]
    st.success("Old JD loaded")

# ---------------- Skills ----------------
st.subheader("Required Skills")
skills_input = st.text_input(
    "Enter skills (comma separated)",
    placeholder="Python, SQL, AWS"
)

if skills_input:
    st.session_state["skills"] = [s.strip().lower() for s in skills_input.split(",")]

    # Update skills in DB if JD already exists
    if "jd_id" in st.session_state:
        supabase.table("job_requirements") \
            .update({"skills": st.session_state["skills"]}) \
            .eq("id", st.session_state["jd_id"]) \
            .execute()

    st.success("Skills saved")

# ---------------- JD Upload ----------------
st.header("Job Description")
jd_file = st.file_uploader("Upload JD (PDF)", type=["pdf"])

if jd_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(jd_file.read())
        jd_text = extract_text(tmp.name)

    jd_id = str(uuid.uuid4())

    supabase.table("job_requirements").insert({
        "id": jd_id,
        "client_id": st.session_state["recruiter_id"],
        "title": jd_file.name,
        "jd_text": jd_text,
        "skills": st.session_state.get("skills", []),
        "status": "active"
    }).execute()

    st.session_state["jd_text"] = jd_text
    st.session_state["jd_id"] = jd_id

    st.success("JD uploaded and saved")

if "jd_text" not in st.session_state:
    st.stop()

# ---------------- Resume Upload ----------------
st.header("Upload Resumes")

resume_files = st.file_uploader(
    "Upload Resume (PDF/DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

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
            "jd_id": st.session_state["jd_id"],  # 🔥 important
            "resume_name": resume_file.name,
            "email": parsed["email"],
            "phone": parsed["mobile"],
            "experience": parsed["experience"],
            "score": final_score,
            "skills": parsed["skills_found"]
        }).execute()

        st.session_state["uploaded_resumes"].add(resume_file.name)

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
    .eq("jd_id", st.session_state["jd_id"]) \
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

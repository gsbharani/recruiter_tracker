import streamlit as st
import tempfile
import uuid

from supabase_client import supabase
from text_utils import extract_text
from matcher import semantic_score

st.set_page_config("Recruiter JD Matcher", layout="wide")
st.title("🧠 Recruiter JD ↔ Resume Matcher")

# ---------------- Recruiter ----------------
st.header("Recruiter")
recruiter_name = st.text_input("Your Name")

if st.button("Create / Load Recruiter"):
    res = supabase.table("recruiters") \
        .select("*") \
        .eq("name", recruiter_name) \
        .execute()

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
        jd_text = extract_text(tmp.name)

    st.session_state["jd_text"] = jd_text
    st.success("JD uploaded")

if "jd_text" not in st.session_state:
    st.stop()

# ---------------- Resume Upload ----------------
st.header("Upload Resumes")

resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

if resume_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(resume_file.read())
        resume_text = extract_text(tmp.name)

    score = semantic_score(st.session_state["jd_text"], resume_text)

    supabase.table("candidates").insert({
        "id": str(uuid.uuid4()),
        "recruiter_id": st.session_state["recruiter_id"],
        "resume_name": resume_file.name,
        "score": score
    }).execute()

    st.success(f"Resume scored: {score}%")

# ---------------- Ranking ----------------
st.header("📊 Ranked Candidates")

results = supabase.table("candidates") \
    .select("*") \
    .eq("recruiter_id", st.session_state["recruiter_id"]) \
    .order("score", desc=True) \
    .execute()

if results.data:
    st.table([
        {
            "Resume": r["resume_name"],
            "Fit %": r["score"]
        } for r in results.data
    ])

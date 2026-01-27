import streamlit as st
from backend.resume_parser import parse_resume
from backend.storage import upload_resume
from backend.db import save_candidate
import tempfile

st.set_page_config(page_title="Recruiter Tracker", layout="wide")
st.title("Recruiter Hiring & Resume Tracker")

recruiter_id = st.text_input("Recruiter ID (Auth UID)")
uploaded = st.file_uploader("Upload Resume", type=["pdf"])

if uploaded and recruiter_id:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded.read())
        temp_path = tmp.name

    # Parse resume
    parsed = parse_resume(temp_path)

    # Upload resume to storage
    resume_path = upload_resume(uploaded, uploaded.name)

    # Candidate payload
    candidate = {
        "name": uploaded.name.split(".")[0],
        "email": parsed.get("email"),
        "phone": parsed.get("phone"),
        "experience": parsed.get("experience"),
        "resume_url": resume_path,
        "recruiter_id": recruiter_id
    }

    # Save to database
    save_candidate(candidate)
    st.success("Candidate uploaded & saved successfully")

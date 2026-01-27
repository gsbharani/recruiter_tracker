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
with tempfile.NamedTemporaryFile(delete=False) as tmp:
tmp.write(uploaded.read())
parsed = parse_resume(tmp.name)


resume_path = upload_resume(uploaded, uploaded.name)


candidate = {
"name": uploaded.name.split(".")[0],
"email": parsed["email"],
"phone": parsed["phone"],
"experience": parsed["experience"],
"resume_url": resume_path,
"recruiter_id": recruiter_id
}


save_candidate(candidate)
st.success("Candidate uploaded & saved successfully")

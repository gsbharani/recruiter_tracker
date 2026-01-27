import streamlit as st
import tempfile
import os
import re
from supabase import create_client
from dotenv import load_dotenv

# ---------------- LOAD ENV ----------------
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Recruiter Tracker", layout="centered")
st.title("📋 Recruiter Hiring Tracker")

# ---------------- HELPERS ----------------
def parse_resume(file_path):
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except:
        pass

    email = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    phone = re.findall(r"\+?\d[\d\s-]{8,}", text)

    return {
        "email": email[0] if email else "",
        "phone": phone[0] if phone else ""
    }


def upload_resume(uploaded_file, filename):
    file_bytes = uploaded_file.read()
    bucket = "resumes"

    supabase.storage.from_(bucket).upload(
        path=filename,
        file=file_bytes,
        upsert=True
    )

    return supabase.storage.from_(bucket).get_public_url(filename)["publicUrl"]


# ---------------- SESSION ----------------
if "recruiter_id" not in st.session_state:
    st.session_state.recruiter_id = None


# ---------------- RECRUITER REGISTRATION ----------------
if not st.session_state.recruiter_id:
    st.subheader("👤 Recruiter Registration")

    r_name = st.text_input("Name")
    r_email = st.text_input("Email")

    if st.button("Register"):
        if not r_name:
            st.error("Name required")
        else:
            res = supabase.table("recruiters").insert({
                "name": r_name,
                "email": r_email
            }).execute()

            st.session_state.recruiter_id = res.data[0]["id"]
            st.success("Recruiter registered successfully 🎉")
            st.rerun()


# ---------------- CANDIDATE UPLOAD ----------------
if st.session_state.recruiter_id:
    st.divider()
    st.subheader("📄 Add Candidate")

    uploaded = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded.read())
            temp_path = tmp.name

        parsed = parse_resume(temp_path)
        resume_url = upload_resume(uploaded, uploaded.name)

        candidate_name = uploaded.name.replace(".pdf", "")

        if st.button("Save Candidate"):
            supabase.table("candidates").insert({
                "name": candidate_name,
                "email": parsed["email"],
                "phone": parsed["phone"],
                "resume_url": resume_url,
                "recruiter_id": st.session_state.recruiter_id
            }).execute()

            st.success("Candidate saved successfully ✅")

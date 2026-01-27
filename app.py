import streamlit as st
import tempfile
import re
import os
import uuid
from supabase import create_client

# ---------------- CONFIG ----------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

st.set_page_config(page_title="Recruiter Tracker", layout="wide")
st.title("Recruiter Hiring & Resume Tracker")

# ---------------- HELPERS ----------------
def parse_resume(file_path):
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception:
        pass

    email = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    phone = re.findall(r"\+?\d[\d\s-]{8,}", text)

    return {
        "email": email[0] if email else None,
        "phone": phone[0] if phone else None,
        "experience": None
    }

def upload_resume(uploaded_file, filename):
    bucket = "resumes"
    file_bytes = uploaded_file.read()

    try:
        supabase.storage.from_(bucket).upload(
            path=filename,
            file=file_bytes,
            upsert=True
        )
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None

    url_data = supabase.storage.from_(bucket).get_public_url(filename)
    return url_data["publicUrl"]

def save_candidate(data):
    supabase.table("candidates").insert(data).execute()

# ---------------- UI ----------------
recruiter_id = st.text_input("Recruiter ID (UUID)")
uploaded = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

if uploaded and recruiter_id:
    # ✅ Validate UUID AFTER input
    try:
        recruiter_uuid = str(uuid.UUID(recruiter_id))
    except ValueError:
        st.error("Please enter a valid UUID (example: 550e8400-e29b-41d4-a716-446655440000)")
        st.stop()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded.read())
        temp_path = tmp.name

    parsed = parse_resume(temp_path)

    # Make filename unique
    import time
    filename = f"{recruiter_uuid}_{int(time.time())}_{uploaded.name}"

    resume_url = upload_resume(uploaded, filename)

    candidate = {
        "name": uploaded.name.split(".")[0],
        "email": parsed.get("email") or "",
        "phone": parsed.get("phone") or "",
        "experience": parsed.get("experience") or 0,
        "resume_url": resume_url or "",
        "recruiter_id": recruiter_uuid
    }

    save_candidate(candidate)
    st.success("Candidate uploaded & saved successfully 🎉")

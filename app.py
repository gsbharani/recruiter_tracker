import streamlit as st
import tempfile
import uuid
import pandas as pd

from resume_parser import parse_resume
from text_utils import extract_text
from matcher import semantic_score, skill_score
from supabase_client import supabase
from jd_skill_extractor import extract_skills_from_jd

# ---------------- Page Config ----------------
st.set_page_config("Talent Fit Analyzer", layout="wide")
st.title("🧑‍💼✅ Talent Fit Analyzer - Instantly Find the Best Candidates")

# ---------------- Initialize Session State ----------------
for key in ["recruiter_id", "jd_id", "jd_text", "skills", "uploaded_resumes"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "skills" and key != "uploaded_resumes" else ([] if key=="skills" else set())

# ---------------- Recruiter ----------------
st.header("👤 Recruiter")
recruiter_name = st.text_input("Your Name")

if st.button("Create / Load Recruiter"):
    res = supabase.table("recruiters").select("*").eq("name", recruiter_name).execute()
    if res.data:
        recruiter_id = res.data[0]["id"]
    else:
        recruiter = supabase.table("recruiters").insert({"name": recruiter_name}).execute()
        recruiter_id = recruiter.data[0]["id"]
    st.session_state["recruiter_id"] = recruiter_id
    st.success("Recruiter ready ✅")

if not st.session_state["recruiter_id"]:
    st.stop()

# ---------------- Load Existing JDs ----------------
st.header("📄 Job Description")
jds = supabase.table("job_requirements") \
    .select("id, title, jd_text, skills") \
    .eq("client_id", st.session_state["recruiter_id"]) \
    .execute()

jd_map = {jd["title"]: jd for jd in jds.data} if jds.data else {}
selected_jd = st.selectbox("Select JD", ["Create New JD"] + list(jd_map.keys()))

if selected_jd != "Create New JD":
    jd = jd_map[selected_jd]
    st.session_state["jd_text"] = jd["jd_text"]
    st.session_state["skills"] = jd["skills"]
    st.session_state["jd_id"] = jd["id"]
    st.success(f"Loaded JD: {selected_jd} ✅")

# ---------------- JD Upload ----------------
st.header("Upload New JD")
jd_file = st.file_uploader("Upload JD (PDF/DOCX)", type=["pdf","docx"],accept_multiple_files=True)

if jd_file and not st.session_state.get("jd_id"):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(jd_file.read())
        jd_text = extract_text(tmp.name)

    auto_skills = extract_skills_from_jd(jd_text)
    jd_id = str(uuid.uuid4())

    supabase.table("job_requirements").insert({
        "id": jd_id,
        "client_id": st.session_state["recruiter_id"],
        "title": jd_file.name,
        "jd_text": jd_text,
        "skills": auto_skills,
        "status": "active"
    }).execute()

    st.session_state["jd_text"] = jd_text
    st.session_state["skills"] = auto_skills
    st.session_state["jd_id"] = jd_id

    st.info("💡 Suggested skills from JD (editable): " + ", ".join(auto_skills))
    st.success("JD uploaded, 🎯skills extracted, and saved ✅")

# ---------------- Skills ----------------
if st.session_state.get("jd_text"):
    st.subheader("🎯 Skills detected from JD")
    st.caption("Auto-extracted from the job description. Edit only if needed.")
    skills_input = st.text_input(
        label="",
        value=", ".join(st.session_state["skills"]),
        placeholder="Add or remove skills if required"
    )

    if st.button("Save Skills"):
        st.session_state["skills"] = [s.strip().lower() for s in skills_input.split(",")]
        supabase.table("job_requirements") \
            .update({"skills": st.session_state["skills"]}) \
            .eq("id", st.session_state["jd_id"]) \
            .execute()
        st.success("Skills saved ✅")

def normalize_skills(skills):
    return set(s.strip().lower() for s in skills if s)

# ---------------- Resume Upload ----------------
st.header("📂 Upload Resumes")
resume_files = st.file_uploader(
    "Upload Resume (PDF/DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

if resume_files and st.session_state["jd_id"]:
    for resume_file in resume_files:
        # ---- Duplicate check first ----
        existing = supabase.table("candidates") \
            .select("id") \
            .eq("jd_id", st.session_state["jd_id"]) \
            .eq("resume_name", resume_file.name) \
            .execute()

        if existing.data:
            st.warning(f"⚠️ {resume_file.name} already uploaded for this JD")
            continue

        # ---- Parse resume and calculate scores ----
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(resume_file.read())
            resume_path = tmp.name

        resume_text = extract_text(resume_path)
        parsed = parse_resume(resume_path, st.session_state.get("skills", []))

        jd_score = semantic_score(st.session_state["jd_text"], resume_text)
        skill_match = skill_score(resume_text, st.session_state.get("skills", []))
        final_score = round((jd_score * 0.7) + (skill_match * 0.3), 2)

        jd_skills = normalize_skills(st.session_state["skills"])
        candidate_skills = normalize_skills(parsed["skills_found"])
        matched_skills = list(jd_skills & candidate_skills)
        missing_skills = list(jd_skills - candidate_skills)

        supabase.table("candidates").insert({
            "id": str(uuid.uuid4()),
            "recruiter_id": st.session_state["recruiter_id"],
            "jd_id": st.session_state["jd_id"],
            "resume_name": resume_file.name,
            "email": parsed["email"],
            "phone": parsed["mobile"],
            "experience": parsed["experience"],
            "score": final_score,
            "skills": parsed["skills_found"],
            "matched_skills": matched_skills,
            "missing_skills": missing_skills
        }).execute()

        st.session_state["uploaded_resumes"].add(resume_file.name)

        # ---- Display resume scoring ----
        st.markdown(f"""
        **📄 {resume_file.name}**
        - 🧠 JD Match: **{jd_score}%**
        - 🛠 Skill Match: **{skill_match}%**
        - 🎯 Final Score: **{final_score}%**
        - ✅ Matched Skills ({len(matched_skills)}): {", ".join(matched_skills) or "None"}
        - ❌ Missing Skills ({len(missing_skills)}): {", ".join(missing_skills) or "None"}
        """)

# ---------------- Ranking ----------------
st.header("📊 Ranked Candidates")
if st.session_state["jd_id"]:
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
else:
    st.info("Please upload or select a JD first.")

def match_resume_to_jd(resume_skills, jd_skills):
    matched = resume_skills & jd_skills
    missing = jd_skills - resume_skills

    score = round((len(matched) / len(jd_skills)) * 100, 2) if jd_skills else 0

    return {
        "score": score,
        "matched": list(matched),
        "missing": list(missing)
    }

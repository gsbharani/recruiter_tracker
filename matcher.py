from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

def semantic_score(jd_text: str, resume_text: str) -> float:
    jd_emb = model.encode(jd_text, convert_to_tensor=True)
    resume_emb = model.encode(resume_text, convert_to_tensor=True)

    similarity = util.cos_sim(jd_emb, resume_emb).item()
    return round(similarity * 100, 2)

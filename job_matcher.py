import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def load_roles(path="data/job_roles.csv"):
    return pd.read_csv(path)


def rank_roles(clean_resume, found_skills, roles_df, semantic_sims=None):
    """Score every job role and return them sorted from best to worst match.

    Standard score : 0.7 x skill coverage + 0.3 x TF-IDF similarity
    With semantic  : 0.6 x skill coverage + 0.15 x TF-IDF + 0.25 x semantic similarity
    """
    resume_skills = {s for skills in found_skills.values() for s in skills}

    role_texts = roles_df["required_skills"].str.replace(",", " ").tolist()
    vectors = TfidfVectorizer().fit_transform([clean_resume] + role_texts)
    tfidf_sims = cosine_similarity(vectors[0:1], vectors[1:])[0]

    results = []
    for i, row in enumerate(roles_df.itertuples()):
        required = {s.strip() for s in row.required_skills.split(",")}
        matched = required & resume_skills
        missing = required - resume_skills
        coverage = len(matched) / len(required)

        if semantic_sims is not None:
            score = 0.6 * coverage + 0.15 * tfidf_sims[i] + 0.25 * semantic_sims[i]
        else:
            score = 0.7 * coverage + 0.3 * tfidf_sims[i]

        results.append({
            "role": row.role,
            "score": round(score * 100, 1),
            "matched": sorted(matched),
            "missing": sorted(missing),
        })

    return sorted(results, key=lambda r: r["score"], reverse=True)

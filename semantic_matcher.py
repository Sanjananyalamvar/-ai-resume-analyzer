from functools import lru_cache

MODEL_NAME = "all-MiniLM-L6-v2"


def semantic_available():
    """True if the sentence-transformers library is installed."""
    try:
        import sentence_transformers  # noqa: F401
        return True
    except Exception:
        return False


@lru_cache(maxsize=1)
def _load_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)


def _chunks(text, size=120):
    words = text.split()
    return [" ".join(words[i:i + size]) for i in range(0, len(words), size)] or [text]


def semantic_scores(clean_resume, roles_df):
    """Meaning-based similarity (0 to 1) between the resume and each role.

    Returns a list in the same order as roles_df, or None if it cannot run,
    so the app can fall back to the normal score.
    """
    try:
        import numpy as np

        model = _load_model()
        resume_vec = model.encode(_chunks(clean_resume), normalize_embeddings=True).mean(axis=0)
        resume_vec = resume_vec / (np.linalg.norm(resume_vec) or 1.0)

        role_texts = [
            f"Skills required for a {row.role}: " + row.required_skills.replace(",", ", ")
            for row in roles_df.itertuples()
        ]
        role_vecs = model.encode(role_texts, normalize_embeddings=True)
        return [float(max(0.0, s)) for s in role_vecs @ resume_vec]
    except Exception:
        return None

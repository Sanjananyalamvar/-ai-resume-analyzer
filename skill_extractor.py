import re
import pandas as pd

# Different ways people write the same skill
ALIASES = {
    "ml": "machine learning",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "js": "javascript",
    "postgres": "postgresql",
    "tf": "tensorflow",
    "powerbi": "power bi",
    "natural language processing": "nlp",
    "convolutional neural network": "cnn",
    "restful api": "rest api",
    "rest apis": "rest api",
}


def load_skills(path="data/skill_dictionary.csv"):
    return pd.read_csv(path)


def _contains(text, phrase):
    """True if the phrase appears as a whole word or phrase in the text."""
    pattern = r"(?<![a-z0-9+#])" + re.escape(phrase) + r"(?![a-z0-9+#])"
    return re.search(pattern, text) is not None


def extract_skills(clean_resume, skill_df):
    """Return found skills grouped by category, e.g. {'programming': ['python']}."""
    text = clean_resume
    for alias, real in ALIASES.items():
        if _contains(text, alias):
            text += " " + real

    found = {}
    for _, row in skill_df.iterrows():
        if _contains(text, row["skill"]):
            found.setdefault(row["category"], []).append(row["skill"])
    return found
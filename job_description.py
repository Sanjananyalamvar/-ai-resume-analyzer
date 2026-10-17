import pandas as pd

from skill_extractor import extract_skills
from text_cleaner import clean_text

CUSTOM_ROLE_NAME = "Pasted job description"


def build_custom_role(jd_text, skill_df):
    """Turn a pasted job description into a one-row role table.

    Returns (roles_df, found_skills_by_category). Only skills that exist in the
    skill dictionary can be detected in the job description.
    """
    found = extract_skills(clean_text(jd_text), skill_df)
    skills = [s for items in found.values() for s in items]
    df = pd.DataFrame([{"role": CUSTOM_ROLE_NAME, "required_skills": ",".join(skills)}])
    return df, found

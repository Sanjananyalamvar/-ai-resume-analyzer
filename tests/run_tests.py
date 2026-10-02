import sys
from pathlib import Path

# Let Python find the project files one folder up
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
from resume_parser import extract_text
from text_cleaner import clean_text
from skill_extractor import load_skills, extract_skills
from job_matcher import load_roles, rank_roles

cases = pd.read_csv("tests/test_cases.csv")
skill_df, roles_df = load_skills(), load_roles()

rows = []
for _, case in cases.iterrows():
    with open(case["resume"], "rb") as f:
        text = clean_text(extract_text(f, case["resume"]))
    skills = extract_skills(text, skill_df)
    ranked = rank_roles(text, skills, roles_df)
    top = ranked[0]
    rows.append({
        "Test Resume": Path(case["resume"]).stem,
        "Expected Top Role": case["expected_top_role"],
        "Actual Top Role": top["role"],
        "Score": top["score"],
        "Skills Found": sum(len(v) for v in skills.values()),
        "Result": "PASS" if top["role"] == case["expected_top_role"] else "FAIL",
    })

report = pd.DataFrame(rows)
print(report.to_string(index=False))
report.to_csv("tests/testing_sheet.csv", index=False)
print("\nSaved to tests/testing_sheet.csv")
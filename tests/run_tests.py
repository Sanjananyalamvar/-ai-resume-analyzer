import sys
from pathlib import Path

# Let Python find the project files one folder up
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
from job_matcher import load_roles, rank_roles
from resume_parser import NeedsOCRError, extract_text
from skill_extractor import extract_skills, load_skills
from text_cleaner import clean_text

print("Running tests...")

cases = pd.read_csv("tests/test_cases.csv")
skill_df, roles_df = load_skills(), load_roles()

rows = []
for _, case in cases.iterrows():
    row = {"Test Resume": Path(case["resume"]).stem, "Expected Top Role": case["expected_top_role"],
           "Actual Top Role": "-", "Score": "-", "Skills Found": "-"}
    try:
        with open(case["resume"], "rb") as f:
            text = clean_text(extract_text(f, case["resume"]))
    except NeedsOCRError:
        row["Result"] = "SKIP (OCR not installed)"
        rows.append(row)
        continue
    except Exception as e:
        row["Result"] = f"ERROR: {e}"[:60]
        rows.append(row)
        continue

    skills = extract_skills(text, skill_df)
    top = rank_roles(text, skills, roles_df)[0]
    row.update({
        "Actual Top Role": top["role"],
        "Score": top["score"],
        "Skills Found": sum(len(v) for v in skills.values()),
        "Result": "PASS" if top["role"] == case["expected_top_role"] else "FAIL",
    })
    rows.append(row)

report = pd.DataFrame(rows)
print(report.to_string(index=False))
report.to_csv("tests/testing_sheet.csv", index=False)
print("\nSaved to tests/testing_sheet.csv")

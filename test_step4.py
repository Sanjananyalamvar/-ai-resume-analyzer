from resume_parser import extract_text
from text_cleaner import clean_text
from skill_extractor import load_skills, extract_skills
from job_matcher import load_roles, rank_roles

path = "sample_resumes/resume.pdf"

with open(path, "rb") as f:
    raw = extract_text(f, path)

text = clean_text(raw)
skills = extract_skills(text, load_skills())
ranked = rank_roles(text, skills, load_roles())

print("TOP 3 RECOMMENDED ROLES")
for i, r in enumerate(ranked[:3], start=1):
    print(f"{i}. {r['role']} - {r['score']}%")

print("\nALL ROLES")
for r in ranked:
    print(f"\n{r['role']} - {r['score']}%")
    print("  Matched:", ", ".join(r["matched"]) or "none")
    print("  Missing:", ", ".join(r["missing"]) or "none")
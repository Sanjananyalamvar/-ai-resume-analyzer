from resume_parser import extract_text
from text_cleaner import clean_text
from skill_extractor import load_skills, extract_skills
from job_matcher import load_roles, rank_roles
from roadmap_generator import make_roadmap

path = "sample_resumes/resume.pdf"
target_role = "Machine Learning Engineer"   # try other roles too

with open(path, "rb") as f:
    raw = extract_text(f, path)

text = clean_text(raw)
skills = extract_skills(text, load_skills())
ranked = rank_roles(text, skills, load_roles())

result = next(r for r in ranked if r["role"] == target_role)

print(f"Target Role: {target_role}")
print(f"Match Score: {result['score']}%")
print("\nSkills Found:")
for s in result["matched"]:
    print(f"  - {s}")
print("\nMissing Skills:")
for s in result["missing"]:
    print(f"  - {s}")
print("\nSuggested Roadmap:")
for line in make_roadmap(result["missing"]):
    print(f"  {line}")
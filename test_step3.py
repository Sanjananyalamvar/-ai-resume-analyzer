from resume_parser import extract_text
from text_cleaner import clean_text
from skill_extractor import load_skills, extract_skills

path = "sample_resumes/resume.pdf"   # use your real file name

with open(path, "rb") as f:
    raw = extract_text(f, path)

skills = extract_skills(clean_text(raw), load_skills())

total = sum(len(v) for v in skills.values())
print(f"Skills found: {total}")
for category, items in skills.items():
    print(f"  {category}: {', '.join(items)}")
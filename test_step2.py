from resume_parser import extract_text
from text_cleaner import clean_text

path = "sample_resumes/resume.pdf"

with open(path, "rb") as f:
    raw = extract_text(f, path)

print("--- RAW TEXT ---")
print(raw[:500])
print("--- CLEANED TEXT ---")
print(clean_text(raw)[:500])
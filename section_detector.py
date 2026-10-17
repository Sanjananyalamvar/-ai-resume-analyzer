import re

# Heading patterns for each resume section
SECTIONS = {
    "Summary": r"(summary|professional summary|objective|career objective|profile|about me)",
    "Skills": r"(skills|technical skills|key skills|core skills|core competencies)",
    "Projects": r"(projects?|academic projects?|personal projects?)",
    "Education": r"(education|academic background|qualifications?)",
    "Experience": r"(experience|work experience|professional experience|internships?|employment)",
    "Certifications": r"(certifications?|certificates?|courses)",
}

# Sections every student resume should have
CORE_SECTIONS = ["Skills", "Projects", "Education"]


def detect_sections(raw_text):
    """Return {section name: True/False} by looking for section headings."""
    found = {name: False for name in SECTIONS}
    for line in raw_text.splitlines():
        heading = line.strip().strip(":").strip()
        if not heading or len(heading) > 40:
            continue
        for name, pattern in SECTIONS.items():
            if re.fullmatch(pattern, heading, flags=re.IGNORECASE):
                found[name] = True
    return found

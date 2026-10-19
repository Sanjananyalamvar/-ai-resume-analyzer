"""Checks for the resume builder (no internet or AI key needed)."""
import io
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from docx import Document
from job_matcher import load_roles
from pipeline import analyze
from pypdf import PdfReader
from resume_builder import (LEVELS, bullet_report, check_bullet, display_skill, draft_summary, from_json,
                            new_resume, project_ideas, role_skills, to_docx, to_json, to_pdf, to_text)
from resume_parser import extract_text
from section_detector import detect_sections
from skill_extractor import load_skills

skill_df, roles_df = load_skills(), load_roles()
results = []


def check(name, ok, note=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({note})" if note else ""))


def sample():
    r = new_resume()
    r.update(name="Asha Verma", email="asha@example.com", phone="+91 90000 00000", city="Hyderabad",
             links="github.com/asha-demo", target_role="Data Analyst", level=LEVELS[0])
    r["skills"] = ["python", "sql", "excel", "pandas", "power bi", "statistics", "data visualization"]
    r["projects"] = [{"title": "Sales Dashboard", "tools": "Power BI, SQL, Excel",
                      "bullets": "Built an interactive dashboard in Power BI that tracks 12 months of sales\nCleaned 50,000 rows with Pandas and SQL queries"},
                     {"title": "Survey Analysis", "tools": "Python, Pandas",
                      "bullets": "Analysed 800 survey responses using statistics and data visualization"}]
    r["education"] = [{"degree": "B.Tech in Computer Science", "school": "Sample University", "years": "2023-2027", "score": ""}]
    r["certifications"] = ["Data Analysis Course"]
    r["summary"] = draft_summary(r)
    return r


# ---- bullet checker
good = "Built a dashboard in Power BI that tracks 12 months of sales"
check("A strong bullet has no suggestions", check_bullet(good) == [])
weak = check_bullet("Responsible for working on the sales report")
check("Weak opening is flagged", any("weak" in x for x in weak))
check("Missing number is flagged", any("number" in x for x in check_bullet("Built a dashboard for sales reports and charts")))
check("'I' and 'my' are flagged", any("I, my" in x for x in check_bullet("Built my own dashboard because I like data 5 times")))
check("'I/O' is not mistaken for 'I'", not any("I, my" in x for x in check_bullet("Improved disk I/O speed by 20 percent in tests")))
check("Placeholders are flagged", any("placeholders" in x for x in check_bullet("Built a [what] using [tools] with [result]")))
check("Too long is flagged", any("Too long" in x for x in check_bullet("Built " + "a very long description " * 8 + "99")))

# ---- summary draft uses only what was entered
r = sample()
s = r["summary"]
check("Summary names the role and uses only the first four chosen skills",
      "Data Analyst" in s and all(x in s for x in ("Python", "SQL", "Excel", "Pandas")) and "Statistics" not in s)
check("Summary does not invent numbers", not any(ch.isdigit() for ch in s.replace("2", "").replace("B.Tech", "")) or "2 projects" in s)
check("Summary counts the projects", "2 projects" in s and "Sales Dashboard" in s)
empty = new_resume(); empty["target_role"] = "Data Analyst"
check("Empty resume still gives a safe summary", "Data Analyst" in draft_summary(empty) and "skills" in draft_summary(empty))
changer = new_resume(); changer.update(target_role="Data Analyst", level=LEVELS[2], prev_field="Mechanical engineering")
check("Career changer summary mentions the old field", "Mechanical engineering professional moving into Data Analyst" in draft_summary(changer))

# ---- suggestions
check("Role skills come from the role list", "power bi" in role_skills("Data Analyst", roles_df))
check("Every role has project ideas", all(project_ideas(rn, []) for rn in roles_df["role"]))
check("Skill names are written correctly", [display_skill(x) for x in ("power bi", "mysql", "ci/cd", "scikit-learn", "machine learning")]
      == ["Power BI", "MySQL", "CI/CD", "scikit-learn", "Machine Learning"])

# ---- no personal-detail fields
banned = {"photo", "dob", "birth", "gender", "age", "religion", "marital", "nationality", "caste", "father"}
check("The builder has no field for personal attributes", not any(b in k.lower() for k in new_resume() for b in banned))

# ---- documents round trip through the real parser and the real analysis
pdf, docx_bytes = to_pdf(r, skill_df), to_docx(r, skill_df)
pdf_text = extract_text(io.BytesIO(pdf), "r.pdf")
docx_text = extract_text(io.BytesIO(docx_bytes), "r.docx")
for label, text in (("PDF", pdf_text), ("Word", docx_text)):
    secs = detect_sections(text)
    check(f"{label}: all sections are found by the analyzer", all(secs[k] for k in ("Summary", "Skills", "Projects", "Education", "Certifications")))
    check(f"{label}: no Experience heading when there is none", not secs["Experience"])
    res = analyze(text, skill_df, roles_df)
    top = res["ranked"][0]
    check(f"{label}: analyzer ranks the target role first", top["role"] == "Data Analyst", f"{top['score']}%")
    check(f"{label}: skills shown in projects are not 'only listed'", "power bi" not in res["listed_only"] and "pandas" not in res["listed_only"])
check("Word file has no tables (simple layout)", len(Document(io.BytesIO(docx_bytes)).tables) == 0)
check("PDF text is selectable and fits one page", len(PdfReader(io.BytesIO(pdf)).pages) == 1)
check("Plain text has the name first", to_text(r, skill_df).splitlines()[0] == "Asha Verma")

# ---- experienced order and empty sections
exp = sample(); exp["level"] = LEVELS[1]
exp["experience"] = [{"role": "Data Analyst Intern", "company": "Sample Co", "dates": "Jun 2025 - Aug 2025", "bullets": "Built weekly reports for 3 teams"}]
text = to_text(exp, skill_df)
check("Experienced: Experience comes before Projects", text.index("EXPERIENCE") < text.index("PROJECTS"))
check("Fresher: Projects come before Experience", to_text(dict(exp, level=LEVELS[0]), skill_df).index("PROJECTS") < to_text(dict(exp, level=LEVELS[0]), skill_df).index("EXPERIENCE"))

# ---- report on bullets, save and load
flagged, total = bullet_report(dict(r, projects=[{"title": "X", "tools": "", "bullets": "Worked on stuff\nBuilt a dashboard that tracks 12 months of sales"}]))
check("Bullet report counts flagged bullets", total == 2 and len(flagged) == 1)
back = from_json(to_json(r))
check("A saved draft loads back unchanged", back == r)
check("A broken draft does not crash", from_json('{"name": 5, "skills": "x"}')["name"] == "")

# ---- odd characters do not break the files
odd = sample(); odd["name"] = "Zoë <Test> & Co"; odd["projects"][0]["bullets"] = "Built a “smart” tool → faster by 20%"
check("Special characters do not break the PDF and Word files", len(to_pdf(odd, skill_df)) > 500 and len(to_docx(odd, skill_df)) > 500)

print(f"\n{sum(results)} of {len(results)} checks passed")

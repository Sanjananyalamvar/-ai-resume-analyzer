"""Helpers for creating a resume: checks, drafts, and Word/PDF/text output.

Everything here is rule based and works without any AI service. The resume has no
fields for photo, date of birth, gender, religion, marital status or similar details.
"""
import io
import json
import re
from xml.sax.saxutils import escape

LEVELS = ["Fresher (student or recent graduate)", "Experienced", "Career changer"]

ACTION_VERBS = {
    "built", "developed", "designed", "created", "implemented", "analysed", "analyzed", "automated",
    "optimized", "optimised", "led", "managed", "deployed", "trained", "tested", "wrote", "improved",
    "reduced", "increased", "delivered", "launched", "integrated", "migrated", "configured", "cleaned",
    "visualized", "visualised", "presented", "collaborated", "organized", "organised", "researched",
    "evaluated", "documented", "maintained", "monitored", "secured", "debugged", "refactored",
    "streamlined", "coordinated", "mentored", "taught", "prepared", "produced", "resolved", "supported",
    "achieved", "won", "completed", "engineered", "established", "extracted", "forecasted", "generated",
    "identified", "initiated", "modeled", "modelled", "processed", "programmed", "scraped", "simulated",
    "tracked", "translated", "upgraded", "validated", "published", "compared", "applied", "ran",
}
WEAK_START = re.compile(r"^(responsible for|worked on|involved in|helped with|helped in|duties included|"
                        r"assisted in|assisted with|tasked with|was part of)\b")

SPECIAL = {
    "power bi": "Power BI", "scikit-learn": "scikit-learn", "node.js": "Node.js", "vue.js": "Vue.js",
    "next.js": "Next.js", "express.js": "Express.js", "c++": "C++", "c#": "C#", ".net": ".NET",
    "asp.net": "ASP.NET", "tensorflow": "TensorFlow", "pytorch": "PyTorch", "mysql": "MySQL",
    "postgresql": "PostgreSQL", "mongodb": "MongoDB", "sqlite": "SQLite", "github": "GitHub",
    "javascript": "JavaScript", "typescript": "TypeScript", "fastapi": "FastAPI", "xgboost": "XGBoost",
    "lightgbm": "LightGBM", "hugging face": "Hugging Face", "opencv": "OpenCV", "mlflow": "MLflow",
    "pyspark": "PySpark", "dynamodb": "DynamoDB", "bigquery": "BigQuery", "ci/cd": "CI/CD",
    "rest api": "REST API", "a/b testing": "A/B testing", "langchain": "LangChain", "jquery": "jQuery",
    "graphql": "GraphQL", "websockets": "WebSockets", "wordpress": "WordPress", "vs code": "VS Code",
    "sql server": "SQL Server", "ui design": "UI design", "ux design": "UX design", "ios": "iOS",
    "spacy": "spaCy", "nltk": "NLTK", "jmeter": "JMeter", "junit": "JUnit", "testng": "TestNG",
    "github actions": "GitHub Actions", "gitlab": "GitLab", "aws": "AWS", "gcp": "GCP", "s3": "S3",
    "ec2": "EC2", "iam": "IAM", "vpc": "VPC", "siem": "SIEM", "owasp": "OWASP", "jwt": "JWT",
    "oauth": "OAuth", "css": "CSS", "html": "HTML", "sql": "SQL", "nlp": "NLP", "llm": "LLM",
    "rag": "RAG", "cnn": "CNN", "rnn": "RNN", "lstm": "LSTM", "yolo": "YOLO", "etl": "ETL",
    "oop": "OOP", "dbms": "DBMS", "iot": "IoT", "dax": "DAX", "spss": "SPSS", "sas": "SAS",
    "uml": "UML", "dbt": "dbt", "php": "PHP", "xcode": "Xcode", "swiftui": "SwiftUI",
    "jetpack compose": "Jetpack Compose", "bash": "Bash", "json": "JSON", "sass": "Sass",
    "r programming": "R", "c programming": "C", "google analytics": "Google Analytics",
}

CATEGORY_TITLES = {
    "programming": "Programming", "web": "Web", "backend": "Backend", "database": "Databases",
    "data": "Data and Analytics", "ml": "Machine Learning and AI", "bigdata": "Big Data", "cloud": "Cloud",
    "devops": "DevOps", "tools": "Tools", "mobile": "Mobile", "testing": "Testing", "security": "Security",
    "design": "Design", "concepts": "Concepts", "business": "Business", "other": "Other",
}

PROJECT_IDEAS = {
    "Data Analyst": ["Sales dashboard in Power BI with data from SQL", "Clean and analyse a public dataset with Pandas and charts"],
    "Data Scientist": ["House price prediction with regression and feature engineering", "Customer churn classifier with a clear report"],
    "Machine Learning Engineer": ["Train a model and serve it with FastAPI in a Docker container", "Track experiments with MLflow"],
    "AI Engineer": ["A chatbot that answers questions from your own PDFs (RAG)", "A text or image app that uses a hosted LLM API"],
    "NLP Engineer": ["Sentiment classifier for product reviews with Hugging Face", "News article summarizer"],
    "Computer Vision Engineer": ["Object detection on traffic images with YOLO", "Image classifier with a CNN"],
    "MLOps Engineer": ["CI/CD pipeline that tests, builds and deploys a model", "Model monitoring dashboard"],
    "Data Engineer": ["ETL pipeline that loads a public dataset into a database", "Scheduled data workflow with Airflow"],
    "Business Intelligence Developer": ["Star-schema data model with an interactive dashboard", "Automated weekly sales report"],
    "Business Analyst": ["Requirements document and process diagram for a campus app", "User stories and a prioritised backlog for a small product"],
    "Python Developer": ["Flask or Django blog with login", "Web scraper that saves data through a small API"],
    "Java Developer": ["Spring Boot REST API with a MySQL database", "Library management system with tests"],
    ".NET Developer": ["ASP.NET web API for a task manager", "Inventory app with SQL Server"],
    "Frontend Developer": ["Responsive portfolio website", "Weather app that uses a public API"],
    "Backend Developer": ["REST API with authentication and a database", "URL shortener with caching"],
    "Full Stack Developer": ["E-commerce or bookstore app (React, Node.js, MongoDB)", "Task manager with login and REST API"],
    "Mobile App Developer": ["Expense tracker Android app", "Note-taking app with cloud sync"],
    "Flutter Developer": ["Habit tracker app in Flutter", "Recipe app that uses an API"],
    "DevOps Engineer": ["CI/CD pipeline with Jenkins or GitHub Actions that deploys a Docker image", "Infrastructure with Terraform on AWS"],
    "Cloud Engineer": ["Host a website on AWS with a load balancer", "Serverless function that processes uploaded files"],
    "Cybersecurity Analyst": ["Home lab: scan a network and write a vulnerability report", "Analyse traffic with Wireshark and document findings"],
    "Software Tester (QA)": ["Selenium test suite for a public website", "API tests in Postman with a written test plan"],
    "Database Administrator": ["Design and optimise a database for a small business", "Backup and recovery plan with a test"],
    "UI/UX Designer": ["Redesign a mobile app in Figma with user research", "Clickable prototype with usability notes"],
    "Game Developer": ["2D platformer in Unity", "Puzzle game with a score system"],
    "Embedded/IoT Engineer": ["Arduino weather station", "Raspberry Pi sensor logger"],
}


def display_skill(skill):
    return SPECIAL.get(skill, skill.title())


def new_resume():
    return {
        "name": "", "email": "", "phone": "", "city": "", "links": "",
        "target_role": "", "level": LEVELS[0], "years": "", "prev_field": "",
        "summary": "", "skills": [], "projects": [], "experience": [], "education": [],
        "certifications": [], "extra": "",
    }


# ------------------------------------------------------------------ suggestions
def role_skills(role, roles_df):
    row = roles_df[roles_df["role"] == role]
    if row.empty:
        return []
    return [s.strip() for s in row.iloc[0]["required_skills"].split(",")]


def project_ideas(role, skills):
    if role in PROJECT_IDEAS:
        return PROJECT_IDEAS[role]
    use = [display_skill(s) for s in skills[:2]]
    return [f"A small project that uses {' and '.join(use)}"] if use else ["A small project for the role you want"]


def group_skills(skill_names, skill_df):
    """Group chosen skills by category, in the order of the skill dictionary."""
    category = dict(zip(skill_df["skill"], skill_df["category"]))
    groups = {}
    for skill in skill_names:
        groups.setdefault(category.get(skill, "other"), []).append(skill)
    order = list(CATEGORY_TITLES)
    return {c: groups[c] for c in sorted(groups, key=lambda c: order.index(c) if c in order else 99)}


# --------------------------------------------------------------------- checks
def check_bullet(line):
    """Return a list of plain-language suggestions for one resume bullet."""
    text = line.strip().lstrip("-•*· ").strip()
    if not text:
        return []
    low = text.lower()
    words = text.split()
    issues = []
    if "[" in text and "]" in text:
        issues.append("Replace the [placeholders] with real details.")
    weak = WEAK_START.match(low)
    if weak:
        issues.append(f"'{weak.group(0)}' is weak. Start with a strong verb such as Built, Developed, "
                      "Designed, Analysed or Automated.")
    elif words[0].lower().strip(",.;:") not in ACTION_VERBS:
        issues.append("Start with an action verb such as Built, Developed or Analysed.")
    if re.search(r"(?<![\w/])(i|my|me)(?![\w/])", low):
        issues.append("Leave out I, my and me. Resume bullets are written without them.")
    if not re.search(r"\d", text) and "[" not in text:
        issues.append("Add a number or size if you truly have one (users, records, percentage, time saved).")
    if len(words) > 28:
        issues.append("Too long. Keep it to one or two lines (under 28 words).")
    if len(words) < 5:
        issues.append("Too short. Say what you built, with which tools, and the result.")
    return issues


def bullet_lines(text):
    return [ln.strip().lstrip("-•*· ").strip() for ln in text.splitlines() if ln.strip()]


def all_bullets(resume):
    """[(where, bullet)] for every project and experience bullet."""
    out = []
    for p in resume["projects"]:
        out += [(p.get("title") or "Project", b) for b in bullet_lines(p.get("bullets", ""))]
    for e in resume["experience"]:
        out += [(e.get("role") or "Experience", b) for b in bullet_lines(e.get("bullets", ""))]
    return out


def bullet_report(resume):
    """Return (flagged, total) where flagged is [(where, bullet, issues)]."""
    bullets = all_bullets(resume)
    flagged = [(w, b, check_bullet(b)) for w, b in bullets if check_bullet(b)]
    return flagged, len(bullets)


def draft_summary(resume):
    """A first draft that uses only what the person has entered."""
    role = resume["target_role"] or "the role you want"
    level = resume["level"]
    skills = [display_skill(s) for s in resume["skills"][:4]]
    projects = [p for p in resume["projects"] if p.get("title")]
    degree = next((e.get("degree") for e in resume["education"] if e.get("degree")), "")

    if level == LEVELS[1]:
        years = str(resume.get("years", "")).strip()
        parts = [f"Professional with {years} years of experience, targeting {role} roles." if years
                 else f"Professional targeting {role} roles."]
    elif level == LEVELS[2]:
        prev = resume.get("prev_field", "").strip()
        parts = [f"{prev} professional moving into {role}." if prev else f"Professional moving into {role}."]
    else:
        parts = [f"{degree} student aiming for a {role} role." if degree else f"Student aiming for a {role} role."]

    if skills:
        parts.append("Skilled in " + (", ".join(skills[:-1]) + " and " + skills[-1] if len(skills) > 1 else skills[0]) + ".")
    if len(projects) == 1:
        parts.append(f"Built a project: {projects[0]['title']}.")
    elif len(projects) > 1:
        parts.append(f"Completed {len(projects)} projects, including {projects[0]['title']}.")
    parts.append(f"Looking for an opportunity to apply these skills as a {role}.")
    return " ".join(parts)


# --------------------------------------------------------------- text and files
def _contact(resume):
    return " | ".join(x for x in (resume["email"], resume["phone"], resume["city"], resume["links"]) if x.strip())


def _education_line(e):
    parts = [", ".join(x for x in (e.get("degree"), e.get("school")) if x), e.get("years", ""), e.get("score", "")]
    return " | ".join(p for p in parts if p)


def build_sections(resume, skill_df):
    """Return [(heading, items)] in the right order. Each item is ('text'|'bullet'|'bold'|'skills', value)."""
    sections = []
    if resume["summary"].strip():
        sections.append(("Summary", [("text", resume["summary"].strip())]))

    groups = group_skills(resume["skills"], skill_df)
    if groups:
        sections.append(("Skills", [("skills", (CATEGORY_TITLES.get(c, "Other"), ", ".join(display_skill(s) for s in items)))
                                    for c, items in groups.items()]))

    projects = []
    for p in resume["projects"]:
        if not (p.get("title") or p.get("bullets", "").strip()):
            continue
        head = p.get("title", "Project") + (f" | {p['tools']}" if p.get("tools", "").strip() else "")
        projects.append(("bold", head))
        projects += [("bullet", b) for b in bullet_lines(p.get("bullets", ""))]
    if projects:
        sections.append(("Projects", projects))

    experience = []
    for e in resume["experience"]:
        if not (e.get("role") or e.get("company")):
            continue
        head = ", ".join(x for x in (e.get("role"), e.get("company")) if x) + (f" | {e['dates']}" if e.get("dates") else "")
        experience.append(("bold", head))
        experience += [("bullet", b) for b in bullet_lines(e.get("bullets", ""))]
    if experience:
        sections.append(("Experience", experience))

    education = [("text", _education_line(e)) for e in resume["education"] if _education_line(e)]
    if education:
        sections.append(("Education", education))

    certs = [("bullet", c) for c in resume["certifications"] if c.strip()]
    if certs:
        sections.append(("Certifications", certs))

    extra = bullet_lines(resume.get("extra", ""))
    if extra:
        sections.append(("Achievements", [("bullet", b) for b in extra]))

    if resume["level"] == LEVELS[1]:        # experienced: experience before projects
        names = [s[0] for s in sections]
        if "Experience" in names and "Projects" in names and names.index("Projects") < names.index("Experience"):
            i, j = names.index("Projects"), names.index("Experience")
            sections[i], sections[j] = sections[j], sections[i]
    return sections


def to_text(resume, skill_df):
    lines = [resume["name"].strip() or "Your Name"]
    if _contact(resume):
        lines.append(_contact(resume))
    for heading, items in build_sections(resume, skill_df):
        lines += ["", heading.upper()]
        for kind, value in items:
            if kind == "skills":
                lines.append(f"{value[0]}: {value[1]}")
            elif kind == "bullet":
                lines.append(f"- {value}")
            else:
                lines.append(value)
    return "\n".join(lines)


def _safe(text):
    return escape(str(text).encode("cp1252", "replace").decode("cp1252"))


def to_pdf(resume, skill_df):
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

    name = ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=19, leading=22, alignment=1)
    contact = ParagraphStyle("contact", fontName="Helvetica", fontSize=9.5, leading=12, alignment=1, textColor=HexColor("#444444"))
    head = ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=11, leading=13, spaceBefore=8, textColor=HexColor("#1F3A5F"))
    body = ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=13)
    bold = ParagraphStyle("bold", parent=body, fontName="Helvetica-Bold", spaceBefore=3)
    bullet = ParagraphStyle("bullet", parent=body, leftIndent=12, bulletIndent=2)

    story = [Paragraph(_safe(resume["name"].strip() or "Your Name"), name)]
    if _contact(resume):
        story.append(Paragraph(_safe(_contact(resume)), contact))
    for heading, items in build_sections(resume, skill_df):
        story.append(Paragraph(_safe(heading.upper()), head))
        story.append(HRFlowable(width="100%", thickness=0.6, color=HexColor("#999999"), spaceBefore=1, spaceAfter=3))
        for kind, value in items:
            if kind == "skills":
                story.append(Paragraph(f"<b>{_safe(value[0])}:</b> {_safe(value[1])}", body))
            elif kind == "bullet":
                story.append(Paragraph(_safe(value), bullet, bulletText="•"))
            elif kind == "bold":
                story.append(Paragraph(_safe(value), bold))
            else:
                story.append(Paragraph(_safe(value), body))
    story.append(Spacer(1, 2))
    buffer = io.BytesIO()
    SimpleDocTemplate(buffer, pagesize=A4, leftMargin=17 * mm, rightMargin=17 * mm, topMargin=14 * mm,
                      bottomMargin=14 * mm, title=resume["name"] or "Resume").build(story)
    return buffer.getvalue()


def to_docx(resume, skill_df):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor

    doc = Document()
    for section in doc.sections:
        section.left_margin = section.right_margin = Inches(0.75)
        section.top_margin = section.bottom_margin = Inches(0.6)
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(10.5)

    def spaced(paragraph, after=2, before=0):
        paragraph.paragraph_format.space_after = Pt(after)
        paragraph.paragraph_format.space_before = Pt(before)
        return paragraph

    title = spaced(doc.add_paragraph(), after=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(resume["name"].strip() or "Your Name")
    run.bold, run.font.size = True, Pt(20)
    if _contact(resume):
        c = spaced(doc.add_paragraph(), after=4)
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.add_run(_contact(resume)).font.size = Pt(9.5)

    for heading, items in build_sections(resume, skill_df):
        h = spaced(doc.add_paragraph(), after=3, before=8)
        r = h.add_run(heading.upper())
        r.bold, r.font.size, r.font.color.rgb = True, Pt(11), RGBColor(0x1F, 0x3A, 0x5F)
        border = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        for key, val in (("w:val", "single"), ("w:sz", "6"), ("w:space", "1"), ("w:color", "999999")):
            bottom.set(qn(key), val)
        border.append(bottom)
        h._p.get_or_add_pPr().append(border)
        for kind, value in items:
            if kind == "skills":
                para = spaced(doc.add_paragraph())
                para.add_run(f"{value[0]}: ").bold = True
                para.add_run(value[1])
            elif kind == "bullet":
                spaced(doc.add_paragraph(value, style="List Bullet"), after=1)
            elif kind == "bold":
                spaced(doc.add_paragraph(), after=1, before=3).add_run(value).bold = True
            else:
                spaced(doc.add_paragraph(value))
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def to_json(resume):
    return json.dumps(resume, indent=2)


def from_json(text):
    """Load a saved draft. Unknown or missing fields are ignored or filled with defaults."""
    data = json.loads(text)
    resume = new_resume()
    for key in resume:
        if key in data and isinstance(data[key], type(resume[key])):
            resume[key] = data[key]
    return resume

import re
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def _safe(text):
    """Make text safe for the built-in PDF fonts and for the PDF markup."""
    text = str(text).encode("cp1252", "replace").decode("cp1252")
    return escape(text)


def _plain(text):
    """Strip simple markdown from AI text."""
    text = re.sub(r"[*_`]{1,3}", "", text)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    return text


def build_pdf(target, selected, ranked, skills, sections, roadmap, ai_feedback=None):
    """Create the analysis report and return it as PDF bytes."""
    ss = getSampleStyleSheet()
    title = ParagraphStyle("t", parent=ss["Title"], fontSize=20, spaceAfter=6)
    head = ParagraphStyle("h", parent=ss["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=4)
    body = ParagraphStyle("b", parent=ss["Normal"], fontSize=10, leading=14)
    small = ParagraphStyle("s", parent=body, fontSize=8.5, textColor="#555555")

    def P(text, style=body):
        return Paragraph(_safe(text), style)

    story = [
        P("AI Resume Analysis Report", title),
        P(f"Target role: {target}"),
        P(f"Estimated match score: {selected['score']}%"),
        P("Top 3 recommended roles", head),
    ]
    story += [P(f"{i}. {r['role']} - {r['score']}%") for i, r in enumerate(ranked[:3], start=1)]

    story.append(P("Skills found, by category", head))
    if skills:
        story += [P(f"{cat.title()}: {', '.join(items)}") for cat, items in skills.items()]
    else:
        story.append(P("No known skills were found."))

    story.append(P(f"Skill gap for {target}", head))
    story.append(P("Skills you have: " + (", ".join(selected["matched"]) or "none")))
    story.append(P("Missing skills: " + (", ".join(selected["missing"]) or "none")))

    story.append(P("Resume sections", head))
    story.append(P("   ".join(f"{name}: {'found' if ok else 'not found'}" for name, ok in sections.items())))

    story.append(P("Learning roadmap", head))
    if roadmap:
        story += [P(f"Week {item['week']}: {item['topic']}") for item in roadmap]
    else:
        story.append(P("No gaps found for this role."))

    if ai_feedback:
        story.append(P("AI feedback", head))
        for line in _plain(ai_feedback).splitlines():
            if line.strip():
                story.append(P(line.strip()))
                story.append(Spacer(1, 2))

    story.append(Spacer(1, 10))
    story.append(P("This report is for guidance only. Match scores are estimates, not recruiter decisions. "
                   "A missing keyword does not always mean a missing ability.", small))

    buffer = BytesIO()
    SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                      topMargin=18 * mm, bottomMargin=18 * mm,
                      title="AI Resume Analysis Report").build(story)
    return buffer.getvalue()

"""Checks for the 'describe your problem' feature (no AI service needed)."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from job_matcher import load_roles
from problems import PLAYBOOKS, SUPPORT_MESSAGE, diagnose

roles_df = load_roles()
results = []


def check(name, ok, note=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({note})" if note else ""))


ctx = {"target": "Data Analyst", "score": 55.0, "matched": ["python", "sql"], "missing": ["power bi", "excel", "statistics"],
       "listed_only": {"sql"}, "sections": {"Skills": True, "Projects": False, "Education": True, "Summary": False},
       "evidence_on": True, "top_roles": [("Data Analyst", 55.0), ("Data Scientist", 48.2), ("Python Developer", 40.1)]}


def first(text):
    out = diagnose(text, ctx, roles_df)
    return out, (out["matches"][0][0] if out["matches"] else None)


cases = {
    "I am a fresher and I have no projects": "No projects or experience yet",
    "I am not getting any interview calls": "Not getting shortlisted or interview calls",
    "I want to switch from mechanical to data analyst": "Switching to a new field",
    "my skills are not detected": "Skills not detected correctly",
    "the file will not upload and shows an error": "File will not upload or cannot be read",
    "why is my score so low": "My score is low",
    "I have a gap year and many backlogs": "Career gap, backlogs or low marks",
    "I don't know what to write in my resume": "Where to start when creating a resume",
    "how do I write the summary": "Writing the summary",
    "which skills should I list": "Choosing which skills to list",
    "how to describe my project in bullet points": "Writing projects and bullet points",
    "should I put my photo and date of birth": "Photo and personal details",
    "what is ATS": "What an ATS is",
    "is my data safe, is my resume stored": "Privacy and data safety",
    "I feel I am treated unfairly because of my gender": "Feeling treated unfairly",
}
for text, expected in cases.items():
    out, title = first(text)
    check(f"'{text}' -> {expected}", expected in [m[0] for m in out["matches"]], f"got {[m[0] for m in out['matches']]}")

out = diagnose("I feel hopeless and I will never get a job", ctx, roles_df)
check("Distress gets a kind message and no job advice", out["distress"] and out["matches"] == [] and "talk to someone you trust" in SUPPORT_MESSAGE)
out = diagnose("asdf qwer zxcv", ctx, roles_df)
check("Unmatched text gets a helpful fallback", out["fallback"] and not out["matches"])
out = diagnose("I am a fresher with no projects and not getting interview calls", ctx, roles_df)
check("At most two answers are shown", 1 <= len(out["matches"]) <= 2)
text = " ".join(a for _, a in diagnose("I am a fresher with no projects", ctx, roles_df)["matches"])
check("Advice uses the person's own results", "Data Analyst" in text and "power bi" in text)
check("Every playbook has keywords and a title", all(t and k for t, k, _ in PLAYBOOKS))
all_text = " ".join(f(ctx, roles_df) for _, _, f in PLAYBOOKS)
check("Advice never asks people to invent skills", "invent" not in all_text.lower() and "pretend" not in all_text.lower())
print(f"\n{sum(results)} of {len(results)} checks passed")

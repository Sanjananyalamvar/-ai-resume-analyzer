import pandas as pd
import plotly.express as px
import streamlit as st

from resume_parser import extract_text
from text_cleaner import clean_text
from skill_extractor import load_skills, extract_skills
from job_matcher import load_roles, rank_roles
from roadmap_generator import make_roadmap

MAX_FILE_MB = 5

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")
st.title("📄 AI Resume Analyzer and Job Recommendation System")
st.caption("Upload your resume to see how well it matches different job roles.")

roles_df = load_roles()
skill_df = load_skills()

# ---------- 1. Upload and target role ----------
col1, col2 = st.columns(2)
with col1:
    file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])
with col2:
    target = st.selectbox("Select your target role", roles_df["role"])

if file is None:
    st.info("Upload a resume to begin. Your file is processed in memory and is not saved.")
    st.stop()

# ---------- 2. Validate the file ----------
if file.size > MAX_FILE_MB * 1024 * 1024:
    st.error(f"File is too large. Please upload a file under {MAX_FILE_MB} MB.")
    st.stop()
st.success(f"Uploaded: {file.name}")

# ---------- 3. Extract, clean, find skills, match ----------
try:
    raw_text = extract_text(file, file.name)
except Exception as e:
    st.error(f"Could not read this file. {e}")
    st.stop()

text = clean_text(raw_text)
skills = extract_skills(text, skill_df)
ranked = rank_roles(text, skills, roles_df)
selected = next(r for r in ranked if r["role"] == target)

# ---------- 4. Extracted skills ----------
st.header("Extracted skills")
total = sum(len(v) for v in skills.values())
st.write(f"**{total} skills found**")
if skills:
    for category, items in skills.items():
        st.write(f"**{category.title()}:** {', '.join(items)}")
else:
    st.warning("No known skills were found in this resume.")

# ---------- 5. Match score chart ----------
st.header("Match scores for all roles")
scores_df = pd.DataFrame(ranked)
fig = px.bar(scores_df, x="role", y="score", text="score",
             labels={"role": "Job role", "score": "Match score (%)"},
             range_y=[0, 100])
st.plotly_chart(fig, use_container_width=True)

# ---------- 6. Top 3 roles ----------
st.header("Top 3 recommended roles")
for i, r in enumerate(ranked[:3], start=1):
    st.write(f"**{i}. {r['role']}** - {r['score']}%")

# ---------- 7. Missing skills and roadmap ----------
st.header(f"Skill gap for {target}")
st.metric("Match score", f"{selected['score']}%")

left, right = st.columns(2)
with left:
    st.subheader("Skills you have")
    for s in selected["matched"] or ["None found"]:
        st.write(f"- {s}")
with right:
    st.subheader("Missing skills")
    for s in selected["missing"] or ["None, you cover all required skills"]:
        st.write(f"- {s}")

st.subheader("Learning roadmap")
roadmap = make_roadmap(selected["missing"])
if roadmap:
    for line in roadmap:
        st.write(f"- {line}")
else:
    st.write("No gaps found for this role.")

# ---------- 8. Downloadable report ----------
report_lines = [
    "AI RESUME ANALYSIS REPORT",
    "",
    f"Target role: {target}",
    f"Match score: {selected['score']}%",
    "",
    "Skills found: " + (", ".join(selected["matched"]) or "none"),
    "Missing skills: " + (", ".join(selected["missing"]) or "none"),
    "",
    "Top 3 recommended roles:",
    *[f"  {i}. {r['role']} - {r['score']}%" for i, r in enumerate(ranked[:3], start=1)],
    "",
    "Learning roadmap:",
    *[f"  {line}" for line in roadmap],
    "",
    "Note: Scores are estimates, not recruiter decisions.",
]
st.download_button("Download analysis report", "\n".join(report_lines),
                   file_name="resume_report.txt")

# ---------- 9. Responsible AI note ----------
st.divider()
st.caption(
    "This tool is for guidance only. Match scores are estimates, not recruiter "
    "decisions. A missing keyword does not always mean a missing ability. "
    "Only job-related skills are evaluated."
)
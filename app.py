import os

import pandas as pd
import plotly.express as px
import streamlit as st

from job_description import CUSTOM_ROLE_NAME, build_custom_role
from job_matcher import load_roles, rank_roles
from llm_feedback import DEFAULT_MODEL, get_feedback
from report_generator import build_pdf
from resume_parser import extract_text, ocr_available
from roadmap_generator import make_roadmap_with_links
from section_detector import CORE_SECTIONS, detect_sections
from semantic_matcher import semantic_available, semantic_scores
from skill_extractor import extract_skills, load_skills
from text_cleaner import clean_text

MAX_FILE_MB = 5

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")


def get_secret(name, default=None):
    """Read a value from Streamlit secrets, or from environment variables."""
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, default)


# ---------- Sidebar: optional features ----------
st.sidebar.header("Settings")

use_semantic = False
if semantic_available():
    use_semantic = st.sidebar.checkbox(
        "Use semantic matching",
        value=False,
        help="Understands related words (for example 'ML' and 'machine learning'). "
             "The first run downloads a small model and can take a minute.",
    )
else:
    st.sidebar.caption("Semantic matching is not installed, so the standard score is used.")

if ocr_available():
    st.sidebar.caption("Scanned resumes and photos: supported (OCR is on).")
else:
    st.sidebar.caption("Scanned resumes and photos: not supported here (OCR is not installed).")

api_key = get_secret("GROQ_API_KEY")
use_ai = False
if api_key:
    use_ai = st.sidebar.checkbox("Enable AI resume feedback (Groq)", value=False)
    st.sidebar.caption(
        "If enabled, your resume text (without email, phone numbers and links) is sent "
        "to Groq to write feedback. Leave it off if you do not want that."
    )
else:
    st.sidebar.caption("AI feedback is off because no GROQ_API_KEY was found.")

# ---------- Title, upload, target role ----------
st.title("📄 AI Resume Analyzer and Job Recommendation System")
st.caption("Upload your resume to see how well it matches different job roles.")

roles_df = load_roles()
skill_df = load_skills()

col1, col2 = st.columns(2)
with col1:
    file = st.file_uploader("Upload your resume (PDF, DOCX, or a PNG/JPG photo)",
                            type=["pdf", "docx", "png", "jpg", "jpeg"])
with col2:
    mode = st.radio("Match my resume against",
                    ["A job role from the list", "A job description I paste"])
    jd_mode = mode.startswith("A job description")
    if jd_mode:
        jd_text = st.text_area("Paste the job description here", height=170)
        target = CUSTOM_ROLE_NAME
    else:
        jd_text = ""
        target = st.selectbox("Select your target role", roles_df["role"])

if file is None:
    st.info("Upload a resume to begin. Your file is processed in memory and is not saved.")
    st.stop()

if file.size > MAX_FILE_MB * 1024 * 1024:
    st.error(f"File is too large. Please upload a file under {MAX_FILE_MB} MB.")
    st.stop()
st.success(f"Uploaded: {file.name}")

custom_df, jd_found = None, {}
if jd_mode:
    if not jd_text.strip():
        st.info("Paste a job description to compare your resume with it.")
        st.stop()
    custom_df, jd_found = build_custom_role(jd_text, skill_df)
    if not custom_df.iloc[0]["required_skills"]:
        st.warning("No known skills were found in this job description. "
                   "Try pasting the full requirements section.")
        st.stop()

# ---------- Analysis ----------
try:
    raw_text = extract_text(file, file.name)
except Exception as e:
    st.error(f"Could not read this file. {e}")
    st.stop()

text = clean_text(raw_text)
skills = extract_skills(text, skill_df)
sections = detect_sections(raw_text)

semantic_sims = None
if use_semantic:
    with st.spinner("Running semantic matching (the first time can take a minute)..."):
        semantic_sims = semantic_scores(text, roles_df)
    if semantic_sims is None:
        st.warning("Semantic matching could not run here, so the standard score is used.")

ranked = rank_roles(text, skills, roles_df, semantic_sims=semantic_sims)
if jd_mode:
    jd_sims = None
    if semantic_sims is not None:
        jd_sims = semantic_scores(text, custom_df)
    selected = rank_roles(text, skills, custom_df, semantic_sims=jd_sims)[0]
else:
    selected = next(r for r in ranked if r["role"] == target)
roadmap = make_roadmap_with_links(selected["missing"])
total_skills = sum(len(v) for v in skills.values())

# Forget old AI feedback when the resume or role changes
feedback_key = f"{file.name}|{file.size}|{target}|{hash(jd_text)}"
if st.session_state.get("feedback_key") != feedback_key:
    st.session_state["feedback_key"] = feedback_key
    st.session_state["feedback_text"] = None

# ---------- Summary numbers ----------
m1, m2, m3 = st.columns(3)
m1.metric(f"Match score: {target}", f"{selected['score']}%")
m2.metric("Skills found", total_skills)
m3.metric("Best matching role", ranked[0]["role"])

tab_skills, tab_roles, tab_gap, tab_ai, tab_report = st.tabs(
    ["Skills and sections", "Role matches", "Skill gap and roadmap", "AI feedback", "Report"]
)

# ---------- Tab 1: skills and sections ----------
with tab_skills:
    left, right = st.columns(2)
    with left:
        st.subheader("Extracted skills")
        if skills:
            for category, items in skills.items():
                st.write(f"**{category.title()}:** {', '.join(items)}")
        else:
            st.warning("No known skills were found in this resume.")
    with right:
        st.subheader("Skills by category")
        if skills:
            cat_df = pd.DataFrame(
                [{"category": c.title(), "skills": len(v)} for c, v in skills.items()]
            )
            fig_cat = px.pie(cat_df, names="category", values="skills", hole=0.4)
            st.plotly_chart(fig_cat, key="category_chart")

    st.subheader("Resume sections")
    section_cols = st.columns(len(sections))
    for box, (name, present) in zip(section_cols, sections.items()):
        box.write(("✅ " if present else "❌ ") + name)
    missing_core = [n for n in CORE_SECTIONS if not sections[n]]
    if missing_core:
        st.warning("Section headings not found: " + ", ".join(missing_core) +
                   ". Consider adding them so readers and tools can find them.")
    st.caption("Sections are found by their headings, so unusual headings or "
               "multi-column layouts may be missed.")

# ---------- Tab 2: role matches ----------
with tab_roles:
    st.subheader("Best matching roles")
    scores_df = pd.DataFrame(ranked)
    top10 = scores_df.head(10).iloc[::-1]
    fig_scores = px.bar(top10, x="score", y="role", orientation="h", text="score",
                        labels={"role": "Job role", "score": "Match score (%)"},
                        range_x=[0, 100])
    st.plotly_chart(fig_scores, key="score_chart")
    with st.expander(f"See all {len(scores_df)} roles"):
        st.dataframe(scores_df[["role", "score"]])

    st.subheader("Top 3 recommended roles")
    for i, r in enumerate(ranked[:3], start=1):
        st.write(f"**{i}. {r['role']}** - {r['score']}%")
    if semantic_sims is not None:
        st.caption("Scores include semantic matching.")

# ---------- Tab 3: skill gap and roadmap ----------
with tab_gap:
    st.subheader(f"Skill gap for {target}")
    if jd_mode:
        with st.expander("Skills detected in the job description"):
            for category, items in jd_found.items():
                st.write(f"**{category.title()}:** {', '.join(items)}")
            st.caption("Only skills in the skill dictionary can be detected in a job description.")
    have, lack = st.columns(2)
    with have:
        st.markdown("**Skills you have**")
        for s in selected["matched"] or ["None found"]:
            st.write(f"- {s}")
    with lack:
        st.markdown("**Missing skills**")
        for s in selected["missing"] or ["None, you cover all required skills"]:
            st.write(f"- {s}")

    st.subheader("Learning roadmap")
    if roadmap:
        for item in roadmap:
            links = []
            if item["docs"]:
                links.append(f"[Official docs]({item['docs']})")
            links.append(f"[Video tutorials]({item['video']})")
            st.markdown(f"**Week {item['week']}:** {item['topic']}  \n" + " | ".join(links))
    else:
        st.write("No gaps found for this role.")

# ---------- Tab 4: AI feedback ----------
with tab_ai:
    st.subheader("AI resume feedback")
    if not api_key:
        st.info("AI feedback is off. Add GROQ_API_KEY to the app secrets to turn it on.")
    elif not use_ai:
        st.info("Tick 'Enable AI resume feedback' in the sidebar to use this feature.")
    else:
        if st.button("Generate AI feedback"):
            with st.spinner("Writing feedback..."):
                feedback, error = get_feedback(
                    api_key, get_secret("GROQ_MODEL", DEFAULT_MODEL), target,
                    selected["score"], selected["matched"], selected["missing"], raw_text,
                )
            if error:
                st.error(error)
            else:
                st.session_state["feedback_text"] = feedback

    if st.session_state.get("feedback_text"):
        st.markdown(st.session_state["feedback_text"])
        st.caption("AI feedback can contain mistakes. Use it as a suggestion, not a verdict.")

# ---------- Tab 5: report ----------
with tab_report:
    st.subheader("Download your report")
    pdf_bytes = build_pdf(target, selected, ranked, skills, sections, roadmap,
                          st.session_state.get("feedback_text"))
    st.download_button("Download PDF report", data=pdf_bytes,
                       file_name="resume_report.pdf", mime="application/pdf")
    st.caption("If you generated AI feedback, it is included in the report.")

# ---------- Responsible AI note ----------
st.divider()
st.caption(
    "This tool is for guidance only. Match scores are estimates, not recruiter "
    "decisions. A missing keyword does not always mean a missing ability. "
    "Only job-related skills are evaluated."
)

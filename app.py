import os

import pandas as pd
import plotly.express as px
import streamlit as st

from job_description import CUSTOM_ROLE_NAME, build_custom_role
from job_matcher import load_roles, rank_roles
from advice import QUESTIONS, answer as quick_answer
from builder_page import render_builder
from llm_feedback import DEFAULT_MODEL, build_context, chat_reply, get_feedback, polish_text
from pipeline import analyze
from privacy import strip_personal_info
from report_generator import build_pdf
from resume_parser import extract_text, ocr_available
from roadmap_generator import make_roadmap_with_links
from section_detector import CORE_SECTIONS, detect_sections
from semantic_matcher import semantic_available, semantic_scores
from skill_extractor import load_skills
from text_cleaner import clean_text
from usage_limiter import DailyCounter, check_and_record, refund

MAX_FILE_MB = 5          # PDF and DOCX
MAX_IMAGE_MB = 15        # phone photos are often larger
IMAGE_ENDINGS = (".png", ".jpg", ".jpeg")

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")


def get_secret(name, default=None):
    """Read a value from Streamlit secrets, or from environment variables."""
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, default)


@st.cache_resource
def get_daily_counter():
    """One counter shared by every visitor, so the AI key cannot be drained."""
    return DailyCounter()


@st.cache_resource
def get_chat_counter():
    return DailyCounter()


@st.cache_resource
def get_build_counter():
    return DailyCounter()


AI_SESSION_LIMIT = int(get_secret("AI_SESSION_LIMIT", 3))
AI_DAILY_LIMIT = int(get_secret("AI_DAILY_LIMIT", 50))
AI_COOLDOWN_SECONDS = int(get_secret("AI_COOLDOWN_SECONDS", 15))
CHAT_SESSION_LIMIT = int(get_secret("AI_CHAT_LIMIT", 10))
CHAT_DAILY_LIMIT = int(get_secret("AI_CHAT_DAILY_LIMIT", 200))
CHAT_COOLDOWN_SECONDS = int(get_secret("AI_CHAT_COOLDOWN_SECONDS", 3))
BUILD_SESSION_LIMIT = int(get_secret("AI_BUILD_LIMIT", 6))
BUILD_DAILY_LIMIT = int(get_secret("AI_BUILD_DAILY_LIMIT", 100))
BUILD_COOLDOWN_SECONDS = int(get_secret("AI_BUILD_COOLDOWN_SECONDS", 3))
FEEDBACK_URL = get_secret("FEEDBACK_URL")

# ---------- Sidebar: optional features ----------
page = st.sidebar.radio("What do you want to do?", ["Analyze my resume", "Create my resume"])
if FEEDBACK_URL:
    st.sidebar.markdown(f"[Report a problem with the app]({FEEDBACK_URL})")
st.sidebar.divider()
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

use_evidence = st.sidebar.checkbox(
    "Count skills less if they are only listed",
    value=True,
    help="A skill that appears in a project or in experience counts fully. A skill that is only "
         "in a skills list counts 60%, so padding a resume with keywords does not help.",
)

api_key = get_secret("GROQ_API_KEY")
use_ai = False
if api_key:
    use_ai = st.sidebar.checkbox("Enable AI features: feedback and chat (Groq)", value=False)
    st.sidebar.caption(
        "If enabled, your resume text (without contact details and personal details such as "
        "gender or age) is sent to Groq to write feedback and answers. "
        "Leave it off if you do not want that."
    )
else:
    st.sidebar.caption("AI feedback is off because no GROQ_API_KEY was found.")

# ---------- Title, upload, target role ----------
roles_df = load_roles()
skill_df = load_skills()

# ---------- Create my resume ----------
if page == "Create my resume":
    def run_polish(text, kind, role):
        """AI rewrite for the builder, with the same protection as the other AI features."""
        allowed, message = check_and_record(st.session_state, get_build_counter(), BUILD_SESSION_LIMIT,
                                            BUILD_DAILY_LIMIT, BUILD_COOLDOWN_SECONDS, prefix="build")
        if not allowed:
            return None, message
        reply, error = polish_text(api_key, get_secret("GROQ_MODEL", DEFAULT_MODEL), text, kind, role)
        if error:
            refund(st.session_state, get_build_counter(), prefix="build")
            return None, error
        return reply, None

    render_builder(skill_df, roles_df, polish=run_polish if (api_key and use_ai) else None)
    st.stop()

# ---------- Analyze my resume ----------
st.title("📄 AI Resume Analyzer and Job Recommendation System")
st.caption("Upload your resume to see how well it matches different job roles.")

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

limit_mb = MAX_IMAGE_MB if file.name.lower().endswith(IMAGE_ENDINGS) else MAX_FILE_MB
if file.size > limit_mb * 1024 * 1024:
    st.error(f"This file is too large. Please upload one under {limit_mb} MB.")
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

sections = detect_sections(raw_text)

semantic_sims = None
if use_semantic:
    with st.spinner("Running semantic matching (the first time can take a minute)..."):
        semantic_sims = semantic_scores(clean_text(strip_personal_info(raw_text)), roles_df)
    if semantic_sims is None:
        st.warning("Semantic matching could not run here, so the standard score is used.")

analysis = analyze(raw_text, skill_df, roles_df, use_evidence=use_evidence,
                   semantic_sims=semantic_sims)
text, skills, ranked = analysis["text"], analysis["skills"], analysis["ranked"]
weights, listed_only = analysis["weights"], analysis["listed_only"]
if jd_mode:
    jd_sims = None
    if semantic_sims is not None:
        jd_sims = semantic_scores(text, custom_df)
    selected = rank_roles(text, skills, custom_df, semantic_sims=jd_sims,
                          skill_weights=weights)[0]
else:
    selected = next(r for r in ranked if r["role"] == target)
roadmap = make_roadmap_with_links(selected["missing"])
total_skills = sum(len(v) for v in skills.values())

# Forget old AI feedback when the resume or role changes
feedback_key = f"{file.name}|{file.size}|{target}|{hash(jd_text)}"
if st.session_state.get("feedback_key") != feedback_key:
    st.session_state["feedback_key"] = feedback_key
    st.session_state["feedback_text"] = None
    st.session_state["chat_history"] = []
    st.session_state["quick_answer"] = None

# ---------- Summary numbers ----------
m1, m2, m3 = st.columns(3)
m1.metric(f"Match score: {target}", f"{selected['score']}%")
m2.metric("Skills found", total_skills)
m3.metric("Best matching role", ranked[0]["role"])

tab_skills, tab_roles, tab_gap, tab_ai, tab_ask, tab_report = st.tabs(
    ["Skills and sections", "Role matches", "Skill gap and roadmap", "AI feedback",
     "Ask about your resume", "Report"]
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

    if analysis["evidence_on"]:
        all_skills = {sk for items in skills.values() for sk in items}
        with st.expander("Which skills are backed up by a project or experience?"):
            st.write("**Shown in a project or experience:** "
                     + (", ".join(sorted(all_skills - listed_only)) or "none"))
            st.write("**Only listed (count 60%):** " + (", ".join(sorted(listed_only)) or "none"))
    elif use_evidence:
        st.caption("No Projects or Experience heading was found, so skills are not weighted by evidence.")

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
            st.write(f"- {s}" + (" (only listed)" if s in selected["listed_only"] else ""))
        if selected["listed_only"]:
            st.caption("'Only listed' skills are not shown in any project or experience, so they count 60%. "
                       "Add a project that uses them to raise your score.")
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
        st.info("Tick 'Enable AI features' in the sidebar to use this feature.")
    else:
        left_over = max(0, AI_SESSION_LIMIT - st.session_state.get("ai_count", 0))
        st.caption(f"{left_over} of {AI_SESSION_LIMIT} AI requests left in this session.")
        if st.button("Generate AI feedback"):
            allowed, message = check_and_record(st.session_state, get_daily_counter(),
                                                AI_SESSION_LIMIT, AI_DAILY_LIMIT, AI_COOLDOWN_SECONDS)
            if not allowed:
                st.warning(message)
            else:
                with st.spinner("Writing feedback..."):
                    feedback, error = get_feedback(
                        api_key, get_secret("GROQ_MODEL", DEFAULT_MODEL), target,
                        selected["score"], selected["matched"], selected["missing"], raw_text,
                    )
                if error:
                    refund(st.session_state, get_daily_counter())
                    st.error(error)
                else:
                    st.session_state["feedback_text"] = feedback

    if st.session_state.get("feedback_text"):
        st.markdown(st.session_state["feedback_text"])
        st.caption("AI feedback can contain mistakes. Use it as a suggestion, not a verdict.")

# ---------- Tab 5: ask about your resume ----------
with tab_ask:
    st.subheader("Ask about your resume")
    st.write("Tap a question for an instant answer based on your own results.")
    advice_ctx = {
        "target": target, "score": selected["score"], "matched": selected["matched"],
        "missing": selected["missing"], "listed_only": selected["listed_only"],
        "sections": sections, "evidence_on": analysis["evidence_on"],
    }
    for question_text in QUESTIONS:
        if st.button(question_text, key=f"quick_{question_text}"):
            st.session_state["quick_answer"] = (question_text, quick_answer(question_text, advice_ctx, roles_df))
    if st.session_state.get("quick_answer"):
        asked, reply_text = st.session_state["quick_answer"]
        st.markdown(f"**{asked}**")
        st.markdown(reply_text)

    st.divider()
    st.subheader("Chat with the AI coach")
    if not api_key:
        st.info("The chat is off. Add GROQ_API_KEY to the app secrets to turn it on.")
    elif not use_ai:
        st.info("Tick 'Enable AI features' in the sidebar to chat.")
    else:
        history = st.session_state.setdefault("chat_history", [])
        chat_left = max(0, CHAT_SESSION_LIMIT - st.session_state.get("chat_count", 0))
        st.caption(f"{chat_left} of {CHAT_SESSION_LIMIT} chat messages left in this session. "
                   "Ask only about your resume. Answers can contain mistakes.")
        history_box = st.container()
        user_question = st.chat_input("Ask how to improve your resume, for example: How do I show Docker?")
        if user_question:
            allowed, message = check_and_record(st.session_state, get_chat_counter(), CHAT_SESSION_LIMIT,
                                                CHAT_DAILY_LIMIT, CHAT_COOLDOWN_SECONDS, prefix="chat")
            if not allowed:
                st.warning(message)
            else:
                context = build_context(
                    target, selected["score"], selected["matched"], selected["missing"],
                    selected["listed_only"], [n for n, ok in sections.items() if ok],
                    [n for n, ok in sections.items() if not ok], raw_text,
                )
                with st.spinner("Thinking..."):
                    reply, error = chat_reply(api_key, get_secret("GROQ_MODEL", DEFAULT_MODEL),
                                              context, history, user_question)
                if error:
                    refund(st.session_state, get_chat_counter(), prefix="chat")
                    st.error(error)
                else:
                    history.append({"role": "user", "content": user_question})
                    history.append({"role": "assistant", "content": reply})
        with history_box:
            for item in history:
                with st.chat_message(item["role"]):
                    st.markdown(item["content"])

# ---------- Tab 6: report ----------
with tab_report:
    st.subheader("Download your report")
    pdf_bytes = build_pdf(target, selected, ranked, skills, sections, roadmap,
                          st.session_state.get("feedback_text"), selected["listed_only"])
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

"""The 'Create my resume' page: a guided builder that solves the common problems people face
when writing a resume for the first time."""
import streamlit as st

from pipeline import analyze
from problems import SUPPORT_MESSAGE, diagnose
from resume_builder import (LEVELS, bullet_lines, bullet_report, check_bullet, display_skill, draft_summary,
                            from_json, new_resume, project_ideas, role_skills, to_docx, to_json, to_pdf, to_text)
from section_detector import detect_sections

MAX_PROJECTS, MAX_EXPERIENCE, MAX_EDUCATION = 4, 3, 3
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _collect():
    """Read every answer from the page into one resume dictionary."""
    s = st.session_state
    r = new_resume()
    r.update(name=s.get("b_name", ""), email=s.get("b_email", ""), phone=s.get("b_phone", ""),
             city=s.get("b_city", ""), links=s.get("b_links", ""), target_role=s.get("b_role", ""),
             level=s.get("b_level", LEVELS[0]), years=str(s.get("b_years", "")), prev_field=s.get("b_prev", ""),
             summary=s.get("b_summary", ""), extra=s.get("b_extra", ""))
    chosen = list(s.get("b_skills_role", []))
    chosen += [x for x in s.get("b_skills_other", []) if x not in chosen]
    r["skills"] = chosen
    for i in range(int(s.get("b_nproj", 0))):
        r["projects"].append({"title": s.get(f"b_pt_{i}", ""), "tools": s.get(f"b_ptools_{i}", ""),
                              "bullets": s.get(f"b_pbul_{i}", "")})
    for i in range(int(s.get("b_nexp", 0))):
        r["experience"].append({"role": s.get(f"b_er_{i}", ""), "company": s.get(f"b_ec_{i}", ""),
                                "dates": s.get(f"b_ed_{i}", ""), "bullets": s.get(f"b_eb_{i}", "")})
    for i in range(int(s.get("b_nedu", 1))):
        r["education"].append({"degree": s.get(f"b_edeg_{i}", ""), "school": s.get(f"b_esch_{i}", ""),
                               "years": s.get(f"b_eyrs_{i}", ""), "score": s.get(f"b_escore_{i}", "")})
    r["certifications"] = [c.strip() for c in s.get("b_certs", "").splitlines() if c.strip()]
    return r


def _apply(resume, roles_df):
    """Put a saved draft back into the page. Must run before the widgets are drawn."""
    s = st.session_state
    role = resume["target_role"] if resume["target_role"] in set(roles_df["role"]) else roles_df["role"].iloc[0]
    needed = role_skills(role, roles_df)
    s.update(b_name=resume["name"], b_email=resume["email"], b_phone=resume["phone"], b_city=resume["city"],
             b_links=resume["links"], b_role=role, b_level=resume["level"] if resume["level"] in LEVELS else LEVELS[0],
             b_years=resume["years"], b_prev=resume["prev_field"], b_summary=resume["summary"],
             b_extra=resume["extra"], b_certs="\n".join(resume["certifications"]),
             b_skills_role=[x for x in resume["skills"] if x in needed], b_skills_other=list(resume["skills"]),
             b_nproj=min(len(resume["projects"]), MAX_PROJECTS), b_nexp=min(len(resume["experience"]), MAX_EXPERIENCE),
             b_nedu=max(1, min(len(resume["education"]), MAX_EDUCATION)))
    for i, p in enumerate(resume["projects"][:MAX_PROJECTS]):
        s.update({f"b_pt_{i}": p.get("title", ""), f"b_ptools_{i}": p.get("tools", ""), f"b_pbul_{i}": p.get("bullets", "")})
    for i, e in enumerate(resume["experience"][:MAX_EXPERIENCE]):
        s.update({f"b_er_{i}": e.get("role", ""), f"b_ec_{i}": e.get("company", ""),
                  f"b_ed_{i}": e.get("dates", ""), f"b_eb_{i}": e.get("bullets", "")})
    for i, e in enumerate(resume["education"][:MAX_EDUCATION]):
        s.update({f"b_edeg_{i}": e.get("degree", ""), f"b_esch_{i}": e.get("school", ""),
                  f"b_eyrs_{i}": e.get("years", ""), f"b_escore_{i}": e.get("score", "")})


def _context(resume, skill_df, roles_df):
    text = to_text(resume, skill_df)
    res = analyze(text, skill_df, roles_df)
    role = resume["target_role"] or roles_df["role"].iloc[0]
    sel = next(r for r in res["ranked"] if r["role"] == role)
    return {"target": role, "score": sel["score"], "matched": sel["matched"], "missing": sel["missing"],
            "listed_only": sel["listed_only"], "sections": detect_sections(text),
            "evidence_on": res["evidence_on"], "top_roles": [(r["role"], r["score"]) for r in res["ranked"][:3]]}, res, sel


def _bullet_feedback(text):
    for line in bullet_lines(text):
        issues = check_bullet(line)
        if issues:
            st.markdown(f"⚠️ **{line[:80]}**  \n" + "  \n".join(f"- {x}" for x in issues))
        else:
            st.markdown(f"✅ {line[:80]}")


def _use_text(target_key, source_key):
    st.session_state[target_key] = st.session_state[source_key]


def _ai_box(kind, text_key, result_key, button_key, role, polish):
    """Optional AI rewrite. The person always sees the result and chooses whether to use it."""
    if polish is None:
        return
    if st.button("Polish this with AI", key=button_key):
        text = st.session_state.get(text_key, "")
        if not text.strip():
            st.warning("Write something first, then I can polish it.")
        else:
            with st.spinner("Polishing..."):
                reply, error = polish(text, kind, role)
            if error:
                st.error(error)
            else:
                st.session_state[result_key] = reply
    if st.session_state.get(result_key):
        st.markdown("**AI suggestion** (check that every fact is still true):")
        st.markdown(st.session_state[result_key])
        st.button("Use this version", key=f"{button_key}_use", on_click=_use_text, args=(text_key, result_key))


def render_builder(skill_df, roles_df, polish=None):
    st.title("📝 Create my resume")
    st.caption("A step-by-step builder for a clean, simple resume. Nothing is saved on our side: "
               "download your draft to continue later.")

    roles = list(roles_df["role"])
    all_skills = sorted(skill_df["skill"])

    # ---- continue a saved draft (must run before the widgets below are drawn)
    with st.expander("Continue a saved draft"):
        uploaded = st.file_uploader("Upload the draft file you downloaded before (.json)", type=["json"], key="b_load")
        if uploaded is not None:
            marker = f"{uploaded.name}-{uploaded.size}"
            if st.session_state.get("b_loaded") != marker:
                try:
                    _apply(from_json(uploaded.getvalue().decode("utf-8")), roles_df)
                    st.session_state["b_loaded"] = marker
                    st.success("Draft loaded.")
                except Exception:
                    st.session_state["b_loaded"] = marker
                    st.error("That file could not be read as a resume draft.")

    def on_role_change():
        keep = role_skills(st.session_state.get("b_role", roles[0]), roles_df)
        st.session_state["b_skills_role"] = [x for x in st.session_state.get("b_skills_role", []) if x in keep]

    # ---- stuck? describe the problem
    with st.expander("Stuck? Tell us the problem you are facing"):
        st.write("For example: *I don't know what to write*, *I have no experience*, *I don't know which skills to list*.")
        problem = st.text_area("Your problem", key="b_problem", max_chars=600, height=90, label_visibility="collapsed")
        if st.button("Get help", key="b_problem_go"):
            if problem.strip():
                ctx, _, _ = _context(_collect(), skill_df, roles_df)
                st.session_state["b_problem_result"] = diagnose(problem, ctx, roles_df)
            else:
                st.warning("Please describe your problem first.")
        result = st.session_state.get("b_problem_result")
        if result:
            if result["distress"]:
                st.info(SUPPORT_MESSAGE)
            for title, advice in result["matches"]:
                st.markdown(f"**{title}**")
                st.markdown(advice)
            if result["fallback"]:
                st.markdown(result["fallback"])

    tabs = st.tabs(["1 About you", "2 Skills", "3 Projects", "4 Education and more", "5 Summary", "6 Check and download"])

    # ---------------------------------------------------------------- 1 about you
    with tabs[0]:
        left, right = st.columns(2)
        left.text_input("Full name", key="b_name")
        right.text_input("Email", key="b_email")
        left.text_input("Phone", key="b_phone")
        right.text_input("City", key="b_city")
        st.text_input("LinkedIn or GitHub link (optional)", key="b_links")
        st.selectbox("The role you are aiming for", roles, key="b_role", on_change=on_role_change)
        st.selectbox("Your situation", LEVELS, key="b_level")
        level = st.session_state.get("b_level", LEVELS[0])
        if level == LEVELS[1]:
            st.text_input("Years of experience", key="b_years")
        if level == LEVELS[2]:
            st.text_input("Your earlier field (for example Mechanical engineering)", key="b_prev")
        st.info("We do not ask for a photo, date of birth, age, gender, marital status, religion, nationality or caste. "
                "They do not show your skills and can lead to unfair decisions. "
                "If an employer asks for something specific, follow what they ask.")

    role = st.session_state.get("b_role", roles[0])
    needed = role_skills(role, roles_df)

    # ---------------------------------------------------------------- 2 skills
    with tabs[1]:
        st.multiselect(f"Skills a {role} usually needs. Choose only the ones you really have.", needed,
                       key="b_skills_role", format_func=display_skill)
        st.multiselect("Other skills you have", all_skills, key="b_skills_other", format_func=display_skill)
        st.caption("Only list skills you could talk about in an interview. Then show each important skill "
                   "in a project in step 3, because skills that are only listed count less.")

    # ---------------------------------------------------------------- 3 projects
    with tabs[2]:
        st.write("Projects matter most when you have little experience. College mini projects, hackathons and "
                 "self-study projects all count.")
        with st.expander(f"Need project ideas for {role}?"):
            for idea in project_ideas(role, needed):
                st.write(f"- {idea}")
        st.number_input("How many projects?", min_value=0, max_value=MAX_PROJECTS, value=1, step=1, key="b_nproj")
        for i in range(int(st.session_state.get("b_nproj", 1))):
            with st.expander(f"Project {i + 1}", expanded=(i == 0)):
                st.text_input("Project name", key=f"b_pt_{i}")
                st.text_input("Tools you used (separate with commas)", key=f"b_ptools_{i}")
                st.text_area("What did you do? Write one line for each point.", key=f"b_pbul_{i}", height=110,
                             placeholder="Built a ... using ... that ...")
                _bullet_feedback(st.session_state.get(f"b_pbul_{i}", ""))
                _ai_box("bullets", f"b_pbul_{i}", f"b_polres_{i}", f"b_pol_{i}", role, polish)

    # ---------------------------------------------------------------- 4 education and more
    with tabs[3]:
        st.subheader("Experience, internships or jobs")
        st.number_input("How many?", min_value=0, max_value=MAX_EXPERIENCE, value=0, step=1, key="b_nexp")
        for i in range(int(st.session_state.get("b_nexp", 0))):
            with st.expander(f"Experience {i + 1}", expanded=(i == 0)):
                st.text_input("Role", key=f"b_er_{i}")
                st.text_input("Company or organisation", key=f"b_ec_{i}")
                st.text_input("Dates (for example Jun 2025 - Aug 2025)", key=f"b_ed_{i}")
                st.text_area("What did you do? One line for each point.", key=f"b_eb_{i}", height=100)
                _bullet_feedback(st.session_state.get(f"b_eb_{i}", ""))
                _ai_box("bullets", f"b_eb_{i}", f"b_eres_{i}", f"b_epol_{i}", role, polish)
        st.subheader("Education")
        st.number_input("How many entries?", min_value=1, max_value=MAX_EDUCATION, value=1, step=1, key="b_nedu")
        for i in range(int(st.session_state.get("b_nedu", 1))):
            with st.expander(f"Education {i + 1}", expanded=(i == 0)):
                st.text_input("Degree or course", key=f"b_edeg_{i}")
                st.text_input("School or college", key=f"b_esch_{i}")
                st.text_input("Years (for example 2023-2027)", key=f"b_eyrs_{i}")
                st.text_input("CGPA or percentage (optional)", key=f"b_escore_{i}")
        with st.expander("Career gap, backlogs or low marks?"):
            st.write("Be honest and keep it short. Marks are optional, so leave them out if they do not help. "
                     "Put your energy into projects, certificates and recent learning, which you can change. "
                     "Prepare one calm sentence for interviews that explains the gap and what you did during it.")
        st.text_area("Certificates and courses (one per line)", key="b_certs", height=90)
        st.text_area("Achievements, hackathons or awards (one per line, optional)", key="b_extra", height=90)

    # ---------------------------------------------------------------- 5 summary
    with tabs[4]:
        st.write("Two or three short sentences at the top. Write a draft from your answers, then make it your own.")

        def fill_summary():
            st.session_state["b_summary"] = draft_summary(_collect())

        st.button("Write a draft for me", on_click=fill_summary, key="b_fill")
        st.text_area("Summary", key="b_summary", height=130)
        st.caption("Skip empty claims such as 'hard working'. Facts about your skills and projects work better.")
        _ai_box("summary", "b_summary", "b_sumres", "b_sumpol", role, polish)

    # ---------------------------------------------------------------- 6 check and download
    with tabs[5]:
        resume = _collect()
        ctx, res, sel = _context(resume, skill_df, roles_df)
        pdf = to_pdf(resume, skill_df)
        from pypdf import PdfReader
        import io
        pages = len(PdfReader(io.BytesIO(pdf)).pages)
        flagged, total = bullet_report(resume)
        text = to_text(resume, skill_df)

        m1, m2, m3 = st.columns(3)
        m1.metric(f"Match for {role}", f"{sel['score']}%")
        m2.metric("Pages", pages)
        m3.metric("Words", len(text.split()))

        limit = 1 if resume["level"] == LEVELS[0] else 2
        checks = [
            (bool(resume["name"].strip()) and bool(resume["email"].strip()), "Name and email are filled in"),
            (bool(resume["summary"].strip()), "A summary is written"),
            (len(resume["skills"]) >= 5, "At least 5 skills are listed"),
            (bool(resume["projects"] or resume["experience"]), "At least one project or experience is added"),
            (any(e.get("degree") for e in resume["education"]), "Education is filled in"),
            (pages <= limit, f"The resume fits in {limit} page(s)"),
            (not flagged, "Every bullet point is strong" if total else "Bullet points are added"),
        ]
        for ok, label in checks:
            st.markdown(("✅ " if ok else "⚠️ ") + label)
        if res["listed_only"]:
            st.markdown("⚠️ Listed but not shown in any project or experience: **"
                        + ", ".join(display_skill(x) for x in sorted(res["listed_only"]))
                        + "**. Add a project line that uses each one, or remove it.")
        if sel["missing"]:
            st.markdown(f"💡 Skills {role} usually asks for that are not on your resume: **"
                        + ", ".join(display_skill(x) for x in sel["missing"])
                        + "**. Only add them if you really have them.")
        for where, bullet, issues in flagged[:6]:
            st.markdown(f"⚠️ *{where}:* {bullet[:80]}  \n" + "  \n".join(f"- {x}" for x in issues))

        st.divider()
        st.subheader("Download")
        stem = (resume["name"].strip().replace(" ", "_") or "resume")
        d1, d2, d3, d4 = st.columns(4)
        d1.download_button("Word (.docx)", to_docx(resume, skill_df), file_name=f"{stem}.docx", mime=DOCX_MIME, key="b_dl_docx")
        d2.download_button("PDF", pdf, file_name=f"{stem}.pdf", mime="application/pdf", key="b_dl_pdf")
        d3.download_button("Plain text", text, file_name=f"{stem}.txt", key="b_dl_txt")
        d4.download_button("Save draft", to_json(resume), file_name=f"{stem}_draft.json", key="b_dl_json")
        st.caption("Switch to 'Analyze my resume' in the sidebar and upload your PDF to see the full analysis.")
        with st.expander("Preview"):
            st.code(text, language=None)

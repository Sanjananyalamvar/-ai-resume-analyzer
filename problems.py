"""Understands a problem a user describes in their own words and gives practical help.
It uses keyword rules and the user's own results, so it works without any AI service."""
from advice import HONESTY_NOTE, skill_priority

DISTRESS_WORDS = ("hopeless", "depressed", "suicid", "want to die", "kill myself", "worthless",
                  "no point in living", "end my life")

SUPPORT_MESSAGE = (
    "I'm really sorry you are feeling this way. Looking for a job can feel very heavy, and how you feel "
    "matters more than any resume.\n\n"
    "Please talk to someone you trust today, such as a family member, a friend or a teacher. "
    "A counsellor or a local helpline can help too, and if you think you might hurt yourself, "
    "please contact your local emergency number right now.\n\n"
    "When you feel ready, I'm here to help with the resume, one small step at a time."
)


def _list(items, empty):
    return ", ".join(items) if items else empty


def _top_missing(ctx, roles_df, n=3):
    return [s for s, _ in skill_priority(ctx["missing"], roles_df)[:n]]


def _top_roles(ctx):
    return _list([f"{r} ({s}%)" for r, s in ctx.get("top_roles", [])], "none yet")


def _missing_core(ctx):
    return [n for n in ("Skills", "Projects", "Education") if not ctx["sections"].get(n)]


# Each playbook: (title, keywords, function that writes the advice)
def _fresher(ctx, roles_df):
    top = _top_missing(ctx, roles_df)
    return ("Everyone starts here, and recruiters who hire freshers look mainly at projects and skills.\n"
            f"- Build two small projects for **{ctx['target']}**. "
            + (f"Use skills you are missing, such as {_list(top, '')}." if top else "Use the skills you already have.") + "\n"
            "- Put each one under a **Projects** heading with one or two bullets: what you built, the tools, the result.\n"
            "- Count college mini projects, hackathons, certificates and coursework as evidence too.\n"
            "- Only write what you really did.")


def _shortlist(ctx, roles_df):
    return ("There are many reasons you cannot see, so focus on what you can change:\n"
            "- **Match each job.** In the app choose *A job description I paste* and see which skills the job wants. Add only skills you really have.\n"
            f"- **Show skills in projects.** Skills only in a list count less. Yours only listed: {_list(sorted(ctx['listed_only']), 'none, good')}.\n"
            "- **Keep the layout simple:** one column, standard headings, a text PDF (not an image), no skills hidden in pictures.\n"
            "- **Add numbers** to your bullets, for example users, records or percentage improvements.\n"
            f"- Missing main headings: {_list(_missing_core(ctx), 'none')}.\n"
            f"- Roles that fit you best right now: {_top_roles(ctx)}.")


def _switch(ctx, roles_df):
    top = _top_missing(ctx, roles_df)
    return ("Your earlier field is an advantage when you show it the right way.\n"
            f"- Start with the closest role instead of many: {_top_roles(ctx)}.\n"
            f"- For **{ctx['target']}** the main skills to add are: {_list(top, 'none, you cover them')}. Follow the roadmap, one skill a week.\n"
            "- Build two projects using data or problems from your old field. It shows both skills together.\n"
            "- Write one honest line at the top, for example: *Mechanical engineer moving into data analysis, with two completed projects.*")


def _choose(ctx, roles_df):
    return (f"Your resume matches these roles best today: {_top_roles(ctx)}.\n"
            "- Use the scores as a starting point, then pick the role you would enjoy.\n"
            "- Test it: spend one week on a small project for that role.\n"
            f"- Compare the gaps. For **{ctx['target']}** you are missing {len(ctx['missing'])} skill(s).")


def _detect(ctx, roles_df):
    return ("The app only knows 251 skills, written as words.\n"
            "- Write each skill by its normal name, for example *Power BI* or *scikit-learn*. Typos such as *Pyhton* are not found.\n"
            "- Give skills their own **Skills** heading on a separate line.\n"
            "- For scans and photos, a clear straight image helps. A text PDF is best.\n"
            "- Fancy templates can hide text in pictures. Export again as a text PDF.\n"
            "- A skill the app misses does not mean you lack it. Scores are estimates.")


def _file(ctx, roles_df):
    return ("Supported files: PDF and DOCX up to 5 MB, and PNG or JPG photos up to 15 MB.\n"
            "- **Password-protected:** open it, choose Print, then Save as PDF, and upload the new copy.\n"
            "- **Made in Canva or similar:** download it as *PDF Standard* so the text can be selected.\n"
            "- **Scan or photo:** use a straight, bright, sharp picture.\n"
            "- Quick test: if you cannot highlight a word in your PDF with the mouse, it is an image.")


def _score(ctx, roles_df):
    top = _top_missing(ctx, roles_df)
    best = ctx["top_roles"][0] if ctx.get("top_roles") else None
    return (f"Your score for **{ctx['target']}** is {ctx['score']}%. It is 70% skill coverage plus 30% text similarity.\n"
            f"- Main reasons: missing {_list(top, 'nothing')}; only listed (counted 60%): {_list(sorted(ctx['listed_only']), 'none')}.\n"
            + (f"- A low score for one role does not mean low ability. Your best match is **{best[0]}** ({best[1]}%).\n" if best else "")
            + "- Open the *Skill gap and roadmap* tab to see what would raise it.")


def _gap(ctx, roles_df):
    return ("Be honest, because gaps and marks are common and many employers care more about skills.\n"
            "- This app does not score gaps or marks. It only looks at job skills.\n"
            "- Strengthen what you control: two projects, a certificate, and recent learning with dates.\n"
            "- Prepare one calm sentence for interviews that explains the gap and what you did during it.")


def _format(ctx, roles_df):
    return ("A simple resume is read best by people and by software.\n"
            "- One page for freshers, two at most.\n"
            "- One column, standard headings, a plain font, no photo, icons or skill bars.\n"
            "- Save as a text PDF.\n"
            "- Good order: Summary, Skills, Projects, Education, Experience, Certifications.\n"
            f"- Headings I could not find in yours: {_list(_missing_core(ctx), 'none of the main ones')}.")


def _learn(ctx, roles_df):
    top = _top_missing(ctx, roles_df)
    return (f"Start with {_list(top, 'a project that proves the skills you already have')}.\n"
            "- Learn one skill a week and build something small with it before moving on.\n"
            "- The *Skill gap and roadmap* tab has official documentation and video links.\n"
            "- Add each finished project to your resume.")


def _privacy(ctx, roles_df):
    return ("- Your resume is processed in memory and is not saved by the app.\n"
            "- The AI features are off unless you switch them on. If you do, the text is sent to Groq with contact details and personal details such as gender or age removed. A name can still be in it.\n"
            "- Upload a version without your phone number and address if you prefer.")


def _bias(ctx, roles_df):
    return ("I'm sorry. Being treated unfairly is not your fault.\n"
            "- This app scores only job skills. Gender, age, religion, caste, marital status and similar details are removed first, and a test checks that they do not change a score.\n"
            "- What you can control is evidence others can check: projects, a GitHub page and certificates.\n"
            "- If it is happening at college or at work, your placement cell or the relevant authority can help. I cannot give legal advice.")


def _start(ctx, roles_df):
    return ("Use **Create my resume** in the sidebar. It walks you through six small steps:\n"
            "1. About you and the role you want\n"
            "2. Skills (tick only the ones you really have)\n"
            "3. Projects, with project ideas for your role\n"
            "4. Experience, education and certificates\n"
            "5. A summary written from your own answers\n"
            "6. A check, then download as Word or PDF\n"
            "If you are a fresher, spend most of your time on Skills and Projects. They matter most.")


def _summary_help(ctx, roles_df):
    return ("A summary is two or three short sentences at the top of the resume.\n"
            "- **Formula:** who you are, your main skills, proof (a project or internship), and the role you want.\n"
            f"- **Example:** *Computer science student aiming for a {ctx['target']} role. Skilled in [skill], [skill] and [skill]. "
            "Completed [number] projects, including [project name].*\n"
            "- Skip empty claims such as *hard working* or *team player*. Show facts instead.\n"
            "- In **Create my resume**, step 5 writes a first draft from your own answers.")


def _skills_help(ctx, roles_df):
    needed = sorted(set(ctx["matched"]) | set(ctx["missing"]))
    return (f"For **{ctx['target']}**, the skills this role usually asks for are: {_list(needed, 'shown in the builder')}.\n"
            "- List only skills you could talk about in an interview.\n"
            "- Put the skills the role needs first, then the rest. Group them by type, for example Programming and Databases.\n"
            "- Then show each important skill in a project, because skills that are only listed count less.\n"
            "- Do not list basic things such as typing or MS Word unless the job asks for them.")


def _bullets_help(ctx, roles_df):
    return ("A strong bullet is **action verb + what you built + tools used + result**.\n"
            "- *Built a sales dashboard in Power BI that tracks 12 months of data for 3 teams.*\n"
            "- Avoid weak openings such as *responsible for* or *worked on*. Avoid I, my and me.\n"
            "- Add a real number when you have one: users, records, percentage or time saved. If you have none, say the size.\n"
            "- The builder checks every bullet and tells you what to improve.")


def _personal(ctx, roles_df):
    return ("You do not need a photo, date of birth, age, gender, marital status, religion, nationality, caste or your father's name.\n"
            "- These do not show skills, and they can lead to unfair decisions, so this app never asks for them and removes them before scoring.\n"
            "- Include your name, email, phone, city and a LinkedIn or GitHub link if you have one.\n"
            "- Practice differs by country. If an employer asks for something specific, follow what they ask.")


def _ats(ctx, roles_df):
    return ("An ATS (applicant tracking system) is software that stores resumes and lets recruiters search them.\n"
            "- Use standard headings such as Skills, Projects and Education.\n"
            "- Use a text PDF or a Word file, one column, no tables, pictures or skill bars.\n"
            "- Use the words from the job description, but only for skills you really have. "
            "In the analyzer, choose *A job description I paste* to see which ones you are missing.")


PLAYBOOKS = [
    ("Where to start when creating a resume",
     ["what to write", "where to start my resume", "how to start my resume", "how to create a resume",
      "how to make a resume", "create a resume", "make a resume", "build a resume", "write a resume",
      "first resume", "never made a resume", "blank page", "how to build my resume"], _start),
    ("Writing the summary",
     ["summary", "objective", "about me", "profile section", "career objective"], _summary_help),
    ("Choosing which skills to list",
     ["which skills", "what skills", "skills to list", "skills section", "skills to add", "skills to put",
      "which skill"], _skills_help),
    ("Writing projects and bullet points",
     ["bullet", "describe my project", "how to describe", "achievements", "responsibilities", "action verb",
      "write my project", "explain my project", "project description"], _bullets_help),
    ("Photo and personal details",
     ["photo", "picture", "date of birth", "dob", "marital status", "religion on", "age on my resume",
      "age in resume", "father", "personal details", "gender on"], _personal),
    ("What an ATS is",
     ["what is ats", "applicant tracking", "ats friendly", "ats-friendly", "keywords for ats", "pass ats",
      "ats score"], _ats),
    ("No projects or experience yet",
     ["no project", "no experience", "fresher", "don't have experience", "dont have experience", "no internship",
      "without experience", "first job", "entry level", "entry-level", "no work experience"], _fresher),
    ("Not getting shortlisted or interview calls",
     ["shortlist", "no call", "no response", "not getting interview", "no interview", "rejected", "rejection", " ats",
      "not hearing back", "never hear back", "no replies", "interview call", "not getting selected", "not selected",
      "never selected", "not getting a job", "not getting job", "no job offer", "no offers"], _shortlist),
    ("Switching to a new field",
     ["switch", "career change", "change my career", "different field", "different background", "non-it", "non it",
      "non-technical", "from mechanical", "from civil", "from commerce", "from arts", "transition", "change field",
      "moving into"], _switch),
    ("Not sure which role to choose",
     ["which role", "what role", "confused", "not sure which", "don't know which", "dont know which",
      "what should i become", "which job", "which career", "which field"], _choose),
    ("Skills not detected correctly",
     ["not detected", "not detecting", "not showing", "missing skill", "skill missing", "didn't find", "didnt find",
      "did not find", "wrong skill", "not recognised", "not recognized", "app missed", "not picking"], _detect),
    ("File will not upload or cannot be read",
     ["upload", "cannot read", "can't read", "cant read", "not reading", "error", "won't open", "wont open", "password",
      "corrupt", "damaged", "scanned", "not opening", "too large", "too big"], _file),
    ("My score is low",
     ["low score", "score is low", "why score", "score so low", "bad score", "less score", "score low", "score is less",
      "poor score", "why is my score"], _score),
    ("Career gap, backlogs or low marks",
     ["gap", "break", "backlog", "low cgpa", "low marks", "low percentage", "dropout", "drop out", "arrears",
      "failed", "low grades", "career break"], _gap),
    ("Resume layout and format",
     ["format", "layout", "template", "design", "two column", "two-column", "canva", "one page", "too long",
      "how long", "pages", "font"], _format),
    ("Where to start and how to learn",
     ["where to start", "how to learn", "where do i start", "which course", "no time", "how to start", "learning path",
      "what to learn", "study plan"], _learn),
    ("Privacy and data safety",
     ["privacy", "is it safe", "stored", "store my", "data safe", "secure", "delete my", "who can see",
      "is my resume saved", "leak"], _privacy),
    ("Feeling treated unfairly",
     ["discriminat", "biased", "unfair", "because i am a woman", "because i'm a woman", "because of my gender",
      "because of my age", "because of my caste", "because of my religion", "treated differently",
      "bias against"], _bias),
]

FALLBACK = ("I could not match this to a common problem, so here are good places to start:\n"
            "- Tap one of the quick questions below.\n"
            "- Try describing it with a few more details, for example *I am a fresher with no projects* "
            "or *I am not getting interview calls*.\n"
            "- If the AI coach is switched on, ask it in the chat below.")


def diagnose(text, ctx, roles_df, max_matches=2):
    """Return {'distress': bool, 'matches': [(title, advice)], 'fallback': str or None}."""
    lowered = " " + text.lower() + " "
    if any(word in lowered for word in DISTRESS_WORDS):
        return {"distress": True, "matches": [], "fallback": None}

    scored = []
    for order, (title, keywords, writer) in enumerate(PLAYBOOKS):
        hits = sum(1 for k in keywords if k in lowered)
        if hits:
            scored.append((-hits, order, title, writer))
    scored.sort()
    matches = [(title, writer(ctx, roles_df)) for _, _, title, writer in scored[:max_matches]]
    return {"distress": False, "matches": matches, "fallback": None if matches else FALLBACK}

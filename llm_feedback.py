import re

import requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"   # change with GROQ_MODEL in secrets if Groq retires it

SYSTEM_PROMPT = (
    "You are a careful career coach for students. You review a resume against one target job role. "
    "Use only the information provided. Give practical, specific advice about job-related skills, "
    "projects, education and how the resume is written. "
    "Never comment on or guess gender, age, religion, nationality, marital status, disability or appearance. "
    "Never promise a job or say the candidate will be rejected. "
    "Remind the reader that a missing keyword does not always mean a missing ability. "
    "Keep the answer under 250 words, in this format: "
    "1) Strengths (2 bullets) 2) Gaps for the target role (2-3 bullets) "
    "3) Resume improvements (3 bullets) 4) One next step."
)


def redact(text):
    """Remove emails, phone numbers and links before the text leaves the app."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[email]", text)
    text = re.sub(r"(?:https?://|www\.)\S+|(?:linkedin|github)\.com/\S+", "[link]", text)
    text = re.sub(r"\+?\d[\d\s().-]{8,}\d", "[phone]", text)
    return text


def build_prompt(target, score, matched, missing, resume_text):
    return (
        f"Target role: {target}\n"
        f"Estimated match score: {score}%\n"
        f"Skills found: {', '.join(matched) or 'none'}\n"
        f"Skills missing: {', '.join(missing) or 'none'}\n\n"
        f"Resume text:\n{redact(resume_text)[:6000]}"
    )


def get_feedback(api_key, model, target, score, matched, missing, resume_text):
    """Return (feedback_text, error_message). One of them is always None."""
    body = {
        "model": model or DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(target, score, matched, missing, resume_text)},
        ],
        "temperature": 0.3,
        "max_tokens": 1500,
    }
    try:
        r = requests.post(GROQ_URL, json=body, timeout=45,
                          headers={"Authorization": f"Bearer {api_key}"})
    except requests.RequestException:
        return None, "Could not reach the AI service. Check your internet connection and try again."

    if r.status_code == 401:
        return None, "The API key was rejected. Check GROQ_API_KEY in your secrets."
    if r.status_code in (400, 404):
        return None, ("The AI model name was not accepted. Check the current model list at "
                      "console.groq.com/docs/models and set GROQ_MODEL in your secrets.")
    if r.status_code == 429:
        return None, "Too many requests right now (free limit reached). Wait a minute and try again."
    if r.status_code != 200:
        return None, f"The AI service returned an error (code {r.status_code})."

    try:
        text = r.json()["choices"][0]["message"]["content"]
    except Exception:
        return None, "The AI service sent an unexpected reply."
    if not text or not text.strip():
        return None, "The AI service sent an empty reply. Please try again."
    return text.strip(), None

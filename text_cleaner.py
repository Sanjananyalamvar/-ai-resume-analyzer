import re


def clean_text(text):
    """Lowercase the text and remove unnecessary symbols and extra spaces."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#.\s\-/]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
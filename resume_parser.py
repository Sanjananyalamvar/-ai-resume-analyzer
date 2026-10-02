from pypdf import PdfReader
from docx import Document


def extract_text(file, filename):
    """Extract text from a PDF or DOCX file."""
    name = filename.lower()

    if name.endswith(".pdf"):
        reader = PdfReader(file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif name.endswith(".docx"):
        doc = Document(file)
        text = "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError("Only PDF and DOCX files are supported")

    if not text.strip():
        raise ValueError("No text found. The file may be a scanned image.")
    return text
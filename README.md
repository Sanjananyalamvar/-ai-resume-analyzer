# AI Resume Analyzer and Job Recommendation System

An NLP-based Streamlit app that compares a resume with job roles, shows a match
score, lists missing skills, and generates a simple learning roadmap.

## Features
- Upload a PDF or DOCX resume (processed in memory, never saved)
- Text extraction and cleaning
- Skill detection from a skill dictionary (50+ skills)
- Match scores for 7 job roles using skill coverage and TF-IDF cosine similarity
- Top 3 recommended roles
- Missing skills and a week-by-week learning roadmap
- Downloadable analysis report

## How the match score works
score = 0.7 x skill coverage + 0.3 x TF-IDF cosine similarity

## Tech stack
Python, Streamlit, pypdf, python-docx, pandas, scikit-learn, Plotly

## Setup
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate`
4. Install: `pip install -r requirements.txt`
5. Run: `streamlit run app.py`

## Project structure
app.py, resume_parser.py, text_cleaner.py, skill_extractor.py, job_matcher.py,
roadmap_generator.py, data/ (CSV datasets), sample_resumes/, tests/

## Testing
Run `python tests/run_tests.py` to test three sample resumes.
Results are saved in `tests/testing_sheet.csv`.

## Responsible AI
- Guidance only, not for hiring or rejection decisions
- Scores are estimates, not recruiter decisions
- Only job-related skills are evaluated; no personal attributes are scored
- A missing keyword does not always mean a missing ability

## Limitations
- Keyword matching can miss synonyms and unusual wording
- Scanned (image) PDFs cannot be read
- The skill dictionary and job roles are small and manually created

## Author
Your name, your college, year
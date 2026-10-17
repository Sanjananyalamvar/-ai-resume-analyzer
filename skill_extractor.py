import re

import pandas as pd

# Other ways people write a skill -> the name used in skill_dictionary.csv
# A value can be one skill or a tuple of skills.
ALIASES = {
    "ml": "machine learning", "sklearn": "scikit-learn", "scikit learn": "scikit-learn",
    "large language model": "llm", "large language models": "llm", "llms": "llm",
    "retrieval augmented generation": "rag", "gen ai": "generative ai", "genai": "generative ai",
    "natural language processing": "nlp", "convolutional neural network": "cnn",
    "convolutional neural networks": "cnn", "yolov3": "yolo", "yolov5": "yolo",
    "yolov7": "yolo", "yolov8": "yolo", "tf": "tensorflow",
    "powerbi": "power bi", "ms excel": "excel", "microsoft excel": "excel",
    "data viz": "data visualization", "data visualisation": "data visualization",
    "exploratory data analysis": "data analysis", "eda": "data analysis",
    "js": "javascript", "ts": "typescript", "html5": "html", "css3": "css",
    "reactjs": "react", "react.js": "react", "nodejs": "node.js", "node js": "node.js",
    "expressjs": "express.js", "vuejs": "vue.js", "vue": "vue.js", "nextjs": "next.js",
    "angularjs": "angular", "tailwind": "tailwind css",
    "restful api": "rest api", "restful apis": "rest api", "rest apis": "rest api",
    "restful web services": "rest api",
    "springboot": "spring boot", "spring-boot": "spring boot",
    "dotnet": ".net", ".net core": ".net",
    "postgres": "postgresql", "postgre sql": "postgresql", "mongo db": "mongodb", "mongo": "mongodb",
    "ms sql": "sql server", "mssql": "sql server", "microsoft sql server": "sql server",
    "stored procedure": "stored procedures",
    "k8s": "kubernetes", "amazon web services": "aws", "google cloud": "gcp",
    "google cloud platform": "gcp", "microsoft azure": "azure",
    "ci cd": "ci/cd", "cicd": "ci/cd", "continuous integration": "ci/cd",
    "vscode": "vs code", "visual studio code": "vs code", "colab": "google colab",
    "jupyter notebook": "jupyter", "jupyter notebooks": "jupyter",
    "object oriented programming": "oop", "object-oriented programming": "oop",
    "dsa": ("data structures", "algorithms"),
    "data structures and algorithms": ("data structures", "algorithms"),
    "database management system": "dbms", "database management systems": "dbms",
    "unit tests": "unit testing", "automation testing": "test automation",
    "pen testing": "penetration testing", "infosec": "information security",
    "ui/ux": ("ui design", "ux design"), "ux/ui": ("ui design", "ux design"),
    "adobe photoshop": "photoshop", "c language": "c programming",
    "embedded c": ("c programming", "embedded systems"),
}

# A tool implies the skill it is built on (a Django project means Python was used).
IMPLIES = {
    "mysql": "sql", "postgresql": "sql", "sqlite": "sql", "sql server": "sql",
    "pyspark": "spark",
    "django": "python", "flask": "python", "fastapi": "python",
    "pandas": "python", "numpy": "python",
    "react": "javascript", "vue.js": "javascript", "node.js": "javascript",
    "express.js": "javascript", "next.js": "javascript",
    "spring boot": "java", "hibernate": "java",
    "scikit-learn": "machine learning", "xgboost": "machine learning", "lightgbm": "machine learning",
    "tensorflow": "deep learning", "pytorch": "deep learning", "keras": "deep learning",
}

# Words that are also normal English: skip the skill when it is used in its everyday sense.
EXCLUDE_AFTER = {
    "excel": "in|at|as|under|during|academically",
    "react": "to|quickly|fast|well|positively",
    "regression": "testing|tests",
}


def load_skills(path="data/skill_dictionary.csv"):
    return pd.read_csv(path)


def _contains(text, phrase):
    """True if the phrase appears as a whole word or phrase in the text."""
    pattern = r"(?<![a-z0-9+#])" + re.escape(phrase) + r"(?![a-z0-9+#])"
    if phrase in EXCLUDE_AFTER:
        pattern += r"(?!\s+(?:" + EXCLUDE_AFTER[phrase] + r")\b)"
    return re.search(pattern, text) is not None


def extract_skills(clean_resume, skill_df):
    """Return found skills grouped by category, e.g. {'programming': ['python']}."""
    text = clean_resume
    for alias, real in ALIASES.items():
        if _contains(text, alias):
            for skill in ((real,) if isinstance(real, str) else real):
                text += " " + skill

    known = dict(zip(skill_df["skill"], skill_df["category"]))
    found_set = {s for s in known if _contains(text, s)}
    for skill, base in IMPLIES.items():
        if skill in found_set and base in known:
            found_set.add(base)

    found = {}
    for skill in skill_df["skill"]:
        if skill in found_set:
            found.setdefault(known[skill], []).append(skill)
    return found

from urllib.parse import quote_plus

import pandas as pd

# Official learning pages (only well-known, stable addresses)
DOCS = {
    "python": "https://docs.python.org/3/tutorial/",
    "numpy": "https://numpy.org/doc/stable/user/absolute_beginners.html",
    "pandas": "https://pandas.pydata.org/docs/getting_started/",
    "matplotlib": "https://matplotlib.org/stable/tutorials/index.html",
    "scikit-learn": "https://scikit-learn.org/stable/user_guide.html",
    "pytorch": "https://pytorch.org/tutorials/",
    "tensorflow": "https://www.tensorflow.org/tutorials",
    "keras": "https://keras.io/getting_started/",
    "hugging face": "https://huggingface.co/learn",
    "transformers": "https://huggingface.co/docs/transformers/index",
    "opencv": "https://docs.opencv.org/4.x/d9/df8/tutorial_root.html",
    "fastapi": "https://fastapi.tiangolo.com/tutorial/",
    "flask": "https://flask.palletsprojects.com/",
    "django": "https://docs.djangoproject.com/en/stable/intro/tutorial01/",
    "docker": "https://docs.docker.com/get-started/",
    "kubernetes": "https://kubernetes.io/docs/tutorials/",
    "mlflow": "https://mlflow.org/docs/latest/",
    "git": "https://git-scm.com/book/en/v2",
    "github": "https://docs.github.com/en/get-started",
    "streamlit": "https://docs.streamlit.io/",
    "sql": "https://www.w3schools.com/sql/",
    "postgresql": "https://www.postgresql.org/docs/current/tutorial.html",
    "power bi": "https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-getting-started",
    "react": "https://react.dev/learn",
    "typescript": "https://www.typescriptlang.org/docs/",
    "javascript": "https://developer.mozilla.org/en-US/docs/Learn_web_development",
    "html": "https://developer.mozilla.org/en-US/docs/Learn_web_development",
    "css": "https://developer.mozilla.org/en-US/docs/Learn_web_development",
    "node.js": "https://nodejs.org/en/learn",
    "java": "https://dev.java/learn/",
    "spring boot": "https://spring.io/guides",
    "kotlin": "https://kotlinlang.org/docs/getting-started.html",
    "flutter": "https://docs.flutter.dev/get-started",
    "android": "https://developer.android.com/courses",
    "selenium": "https://www.selenium.dev/documentation/",
    "pytest": "https://docs.pytest.org/",
    "terraform": "https://developer.hashicorp.com/terraform/tutorials",
    "ansible": "https://docs.ansible.com/",
    "kafka": "https://kafka.apache.org/documentation/",
    "spark": "https://spark.apache.org/docs/latest/",
    "airflow": "https://airflow.apache.org/docs/",
    "aws": "https://aws.amazon.com/getting-started/",
    "azure": "https://learn.microsoft.com/en-us/azure/",
    "gcp": "https://cloud.google.com/docs",
    "figma": "https://help.figma.com/",
    "tableau": "https://www.tableau.com/learn/training",
    "redis": "https://redis.io/docs/latest/",
    "mongodb": "https://www.mongodb.com/docs/manual/tutorial/getting-started/",
}


def _topic(skill, topics):
    return topics.get(skill) or f"{skill.title()}: learn the basics and build one small project"


def load_topics(path="data/learning_topics.csv"):
    """Return a dictionary: skill -> what to learn."""
    df = pd.read_csv(path)
    return dict(zip(df["skill"], df["learning_topic"]))


def make_roadmap(missing_skills, topics=None):
    """Plain text plan: ['Week 1: ...', 'Week 2: ...']."""
    topics = topics or load_topics()
    return [f"Week {week}: {_topic(skill, topics)}"
            for week, skill in enumerate(missing_skills, start=1)]


def video_link(skill):
    query = quote_plus(f"{skill} tutorial for beginners")
    return f"https://www.youtube.com/results?search_query={query}"


def make_roadmap_with_links(missing_skills, topics=None):
    """Week-by-week plan where each item has a topic, a docs link and a video search link."""
    topics = topics or load_topics()
    return [{
        "week": week,
        "skill": skill,
        "topic": _topic(skill, topics),
        "docs": DOCS.get(skill),
        "video": video_link(skill),
    } for week, skill in enumerate(missing_skills, start=1)]

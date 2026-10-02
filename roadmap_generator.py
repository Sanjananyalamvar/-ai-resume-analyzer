import pandas as pd


def load_topics(path="data/learning_topics.csv"):
    """Return a dictionary: skill -> what to learn."""
    df = pd.read_csv(path)
    return dict(zip(df["skill"], df["learning_topic"]))


def make_roadmap(missing_skills, topics=None):
    """Turn a list of missing skills into a week-by-week plan."""
    topics = topics or load_topics()
    plan = []
    for week, skill in enumerate(missing_skills, start=1):
        topic = topics.get(skill, f"Learn {skill}")
        plan.append(f"Week {week}: {topic}")
    return plan
import pandas as pd

skills = pd.read_csv("data/skill_dictionary.csv")
roles = pd.read_csv("data/job_roles.csv")
topics = pd.read_csv("data/learning_topics.csv")

known = set(skills["skill"])
print(f"Skills in dictionary: {len(known)}")
print(f"Roles: {len(roles)}")

if skills["skill"].duplicated().any():
    print("PROBLEM: duplicate skills ->", list(skills[skills['skill'].duplicated()]["skill"]))

for _, row in roles.iterrows():
    required = [s.strip() for s in row["required_skills"].split(",")]
    bad = [s for s in required if s not in known]
    if bad:
        print(f"PROBLEM in {row['role']}: not in dictionary -> {bad}")

print(f"Skills without a learning topic: {len(known - set(topics['skill']))} (fine, they get a default topic)")
print("Check complete")

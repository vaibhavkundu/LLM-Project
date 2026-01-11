import re
from datetime import datetime
from langchain_community.document_loaders import Docx2txtLoader

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10,
    "nov": 11, "dec": 12
}

DATE_REGEX = re.compile(
    r"\(\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\s*-\s*"
    r"(Present|Current|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{4})?\s*\)",
    re.IGNORECASE
)


def normalize_text(text):
    text = (
        text.replace("’", "'")
            .replace("‘", "'")
            .replace("–", "-")
            .replace("—", "-")
    )
    return re.sub(r"'(\d{2})", lambda m: f"20{m.group(1)}", text)


def parse_date(token):
    token = token.lower()
    if "present" in token or "current" in token:
        return datetime.today()
    m, y = token.split()
    return datetime(int(y), MONTHS[m[:3]], 1)


def months_between(start, end):
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


def extract_resume_text(file_path):
    loader = Docx2txtLoader(file_path)
    docs = loader.load()
    text = "\n".join(d.page_content for d in docs)
    return normalize_text(text)


def extract_experience(resume_text):
    experiences = []

    for line in resume_text.split("\n"):
        m = DATE_REGEX.search(line)
        if not m:
            continue

        start = parse_date(f"{m.group(1)} {m.group(2)}")

        if m.group(3).lower() in ["present", "current"]:
            end = datetime.today()
        else:
            end = parse_date(f"{m.group(3)} {m.group(4)}")

        experiences.append((start, end))

    return experiences


def total_experience_months(experiences):
    timeline = set()
    for s, e in experiences:
        cur = datetime(s.year, s.month, 1)
        end = datetime(e.year, e.month, 1)
        while cur <= end:
            timeline.add((cur.year, cur.month))
            cur = datetime(cur.year + (cur.month == 12), (cur.month % 12) + 1, 1)
    return len(timeline)


def format_ym(months):
    return f"{months//12} years {months%12} months"

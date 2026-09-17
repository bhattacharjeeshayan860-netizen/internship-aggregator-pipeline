"""Tech keyword scorer — returns a 0–100 match score for DS/ML/SWE internships.

Scoring is weighted: high-value keywords (3 pts) > medium (2 pts) > general (1 pt).
The score is normalised against a practical ceiling so everyday DS roles score
in the 40–80 range and exact-profile matches push toward 90+.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# ── Keyword weight map ───────────────────────────────────────────────────────
# Format: {keyword_lowercase: weight_points}
# Keywords are matched as substrings in the lowercased title + description.

KEYWORDS: dict[str, int] = {
    # ── Profile-exact matches (3 pts) ─────────────────────────────────────────
    "data science": 3,
    "data scientist": 3,
    "machine learning": 3,
    "mlops": 3,
    "deep learning": 3,
    "python": 3,
    "sql": 3,
    "pandas": 3,
    "scikit-learn": 3,
    "sklearn": 3,
    "xgboost": 3,
    "fastapi": 3,
    "docker": 3,
    "mlflow": 3,
    # ── Strong matches (2 pts) ────────────────────────────────────────────────
    "java": 2,
    "spring boot": 2,
    "microservices": 2,
    "tensorflow": 2,
    "pytorch": 2,
    "spark": 2,
    "airflow": 2,
    "kubernetes": 2,
    "aws": 2,
    "gcp": 2,
    "azure": 2,
    "numpy": 2,
    "nlp": 2,
    "llm": 2,
    "large language model": 2,
    "transformer": 2,
    "hugging face": 2,
    "langchain": 2,
    "feature engineering": 2,
    "data pipeline": 2,
    "etl": 2,
    "dbt": 2,
    "streamlit": 2,
    "fastai": 2,
    "ray": 2,
    "polars": 2,
    "postgres": 2,
    "postgresql": 2,
    "mongodb": 2,
    "redis": 2,
    "kafka": 2,
    "grafana": 2,
    "prometheus": 2,
    # ── Useful signals (1 pt) ─────────────────────────────────────────────────
    "api": 1,
    "rest": 1,
    "git": 1,
    "jupyter": 1,
    "matplotlib": 1,
    "seaborn": 1,
    "plotly": 1,
    "vector": 1,
    "embedding": 1,
    "a/b testing": 1,
    "ab testing": 1,
    "statistical": 1,
    "statistics": 1,
    "regression": 1,
    "classification": 1,
    "clustering": 1,
    "neural network": 1,
    "computer vision": 1,
    "recommendation": 1,
    "dask": 1,
    "gradio": 1,
    "ci/cd": 1,
    "github actions": 1,
    "terraform": 1,
    "bash": 1,
    "linux": 1,
}

# Practical score ceiling (sum of highest-weighted keywords for a realistic role)
SCORE_CEILING = 50

# ── Stipend extraction ───────────────────────────────────────────────────────
# Currency symbol is REQUIRED — bare numbers are never treated as compensation.
# This prevents job IDs, day counts, etc. from being misread as pay rates.
STIPEND_RE = re.compile(
    r"(?P<currency>\$|£|€|CAD|USD|GBP|SGD|AUD|INR)\s*"
    r"(?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+)"
    r"(?:\s*[-–]\s*(?:\$|£|€|CAD|USD|GBP|SGD|AUD|INR)?\s*\d[\d,]*(?:\.\d{1,2})?)?"
    r"\s*(?:per\s+)?(?P<period>hr|hour|hourly|month|monthly|week|weekly|year|yearly|annum|annually)?\b",
    re.IGNORECASE,
)


@dataclass
class ScoredJob:
    tech_score: int
    matched_keywords: list[str] = field(default_factory=list)
    stipend_estimate: str = "Not specified"


def score_job(job: dict) -> ScoredJob:
    """
    Score a raw job dict against the profile keyword list.

    Returns a ScoredJob with:
    - tech_score: 0–100 normalised integer
    - matched_keywords: up to 10 top matched terms
    - stipend_estimate: extracted compensation string or "Not specified"
    """
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()

    total_pts = 0
    matched: list[str] = []

    for kw, pts in KEYWORDS.items():
        if kw in text:
            total_pts += pts
            matched.append(kw)

    score = min(100, round((total_pts / SCORE_CEILING) * 100))
    stipend = _extract_stipend(job.get("description", ""))

    return ScoredJob(
        tech_score=score,
        matched_keywords=matched[:10],
        stipend_estimate=stipend,
    )


def _extract_stipend(description: str) -> str:
    """
    Attempt to extract a human-readable compensation estimate from the description.
    Only matches patterns that include a currency symbol (e.g. $50/hr, £30,000/yr).
    Bare numbers are ignored to prevent false positives from job IDs and counts.
    """
    if not description:
        return "Not specified"

    for m in STIPEND_RE.finditer(description[:2000]):
        currency = m.group("currency")
        if not currency:
            continue  # skip bare numbers — currency symbol required

        raw_amount = m.group("amount").replace(",", "")
        period = (m.group("period") or "").lower()

        try:
            val = int(float(raw_amount))
        except ValueError:
            continue

        # Classify by explicit period keyword first, then by magnitude
        if period in ("hr", "hour", "hourly") or (not period and 10 <= val <= 300):
            return f"~{currency}{val}/hr"
        if period in ("month", "monthly") or (not period and 1_000 <= val <= 25_000):
            return f"~{currency}{val}/mo"
        if period in ("year", "yearly", "annum", "annually") or (not period and 25_000 <= val <= 400_000):
            return f"~{currency}{val}/yr"

    return "Not specified"


"""Resume text → CandidateProfile via keyword matching.

No LLMs, no external APIs — all matching is case-insensitive substring search
against curated lists. Longer/more-specific phrases are matched first to
avoid substring false-positives (e.g. "machine learning" before "learning").
"""
from __future__ import annotations

import re
import logging
from models.resume import CandidateProfile

logger = logging.getLogger(__name__)

# ── Skills ────────────────────────────────────────────────────────────────────
# Ordered longest-first in each group; final sort happens before matching.

SKILL_LIST: list[str] = [
    # DS / ML concepts
    "data science", "machine learning", "deep learning", "mlops",
    "natural language processing", "computer vision", "reinforcement learning",
    "feature engineering", "time series", "recommendation systems",
    "statistical modeling", "a/b testing", "ab testing",
    # ML libraries
    "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras",
    "xgboost", "lightgbm", "catboost", "hugging face", "transformers",
    "langchain", "fastai", "polars", "pyspark",
    # Data libraries
    "pandas", "numpy", "matplotlib", "seaborn", "plotly", "scipy", "dask",
    # Languages
    "python", "sql", "java", "javascript", "typescript", "scala",
    "r", "c++", "c#", "go", "rust", "kotlin", "swift", "bash",
    # Web / API
    "fastapi", "flask", "django", "spring boot", "express",
    "microservices", "rest api", "graphql", "grpc",
    # DevOps / Infra
    "docker", "kubernetes", "terraform", "ansible", "linux", "unix",
    "ci/cd", "github actions", "jenkins", "git", "github", "gitlab",
    # Cloud
    "aws", "gcp", "azure", "google cloud", "databricks",
    "bigquery", "s3", "ec2", "lambda", "redshift", "snowflake",
    # Databases / pipelines
    "postgresql", "postgres", "mysql", "mongodb", "redis",
    "elasticsearch", "kafka", "airflow", "dbt", "etl", "data pipeline",
    # MLOps / experiment tracking
    "mlflow", "wandb", "kubeflow", "dvc", "ray",
    # Visualisation / BI
    "tableau", "power bi", "streamlit", "gradio", "jupyter",
    "grafana", "prometheus",
    # LLM / AI
    "llm", "large language model", "gpt", "bert", "embedding",
    "rag", "retrieval augmented generation", "fine-tuning", "prompt engineering",
    "vector database", "nlp",
    # General
    "api", "spark",
]

# ── Roles ─────────────────────────────────────────────────────────────────────

ROLE_LIST: list[str] = [
    "data scientist", "data analyst", "data engineer",
    "machine learning engineer", "ml engineer", "ai engineer",
    "nlp engineer", "computer vision engineer",
    "research scientist", "research engineer", "applied scientist",
    "software engineer", "software developer",
    "backend engineer", "backend developer",
    "frontend engineer", "frontend developer",
    "full stack engineer", "full stack developer",
    "devops engineer", "platform engineer", "cloud engineer",
    "site reliability engineer",
    "business analyst", "product analyst", "quantitative analyst",
    "data science intern", "machine learning intern",
    "software engineering intern", "ml intern", "ai intern",
]

# ── Education patterns ────────────────────────────────────────────────────────

DEGREE_RE = re.compile(
    r"\b(b\.?tech|b\.?e\.?|b\.?sc?\.?|bca|b\.?s\.?"
    r"|m\.?tech|m\.?e\.?|m\.?sc?\.?|mca|m\.?s\.?"
    r"|bachelor(?:'s)?|master(?:'s)?|ph\.?d\.?|doctorate)\b",
    re.IGNORECASE,
)

FIELD_LIST: list[str] = [
    "computer science", "information technology",
    "electronics", "electrical engineering", "computer engineering",
    "software engineering", "data science", "artificial intelligence",
    "machine learning", "mathematics", "statistics",
    "information systems", "information science",
]

# ── Years of experience ───────────────────────────────────────────────────────

EXP_RE = re.compile(
    r"(\d+)\+?\s*(?:years?|yrs?)[\s\w]{0,15}(?:experience|exp)",
    re.IGNORECASE,
)

# Pre-sort skills: longest first (most specific wins)
_SKILLS_SORTED = sorted(SKILL_LIST, key=len, reverse=True)
_ROLES_SORTED = sorted(ROLE_LIST, key=len, reverse=True)


def parse_candidate_profile(text: str) -> CandidateProfile:
    """Return a CandidateProfile from raw resume text.

    Args:
        text: Plain text extracted from the resume PDF.

    Returns:
        CandidateProfile with skills, roles, education, and experience.
    """
    text_lower = text.lower()

    # ── Skills ────────────────────────────────────────────────────────────────
    skills: list[str] = []
    for skill in _SKILLS_SORTED:
        if skill.lower() in text_lower:
            skills.append(_display_skill(skill))

    # ── Roles ─────────────────────────────────────────────────────────────────
    roles: list[str] = []
    for role in _ROLES_SORTED:
        if role.lower() in text_lower:
            roles.append(role.title())

    # ── Education ─────────────────────────────────────────────────────────────
    education: list[str] = []
    seen_edu: set[str] = set()
    for m in DEGREE_RE.finditer(text):
        window_start = max(0, m.start() - 30)
        window_end = min(len(text), m.end() + 150)
        window = text[window_start:window_end].lower()
        for field in FIELD_LIST:
            if field in window:
                entry = f"{m.group(0).title()} {field.title()}"
                if entry not in seen_edu:
                    seen_edu.add(entry)
                    education.append(entry)
                break
        else:
            entry = m.group(0).title()
            if entry not in seen_edu:
                seen_edu.add(entry)
                education.append(entry)

    # ── Years of experience ───────────────────────────────────────────────────
    years_of_experience: int | None = None
    for m in EXP_RE.finditer(text):
        yrs = int(m.group(1))
        if 0 < yrs <= 40:
            years_of_experience = yrs
            break

    logger.info(
        "Profile parsed: %d skills, %d roles, %d education entries",
        len(skills), len(roles), len(education),
    )
    return CandidateProfile(
        skills=skills,
        roles=roles,
        education=education,
        years_of_experience=years_of_experience,
        text_length=len(text),
    )


# ── Display helpers ───────────────────────────────────────────────────────────

_UPPER = {"sql", "aws", "gcp", "nlp", "llm", "rag", "gpt", "bert",
          "api", "ci/cd", "dbt", "etl", "mlops", "ai", "ml", "swe",
          "ec2", "s3", "dvc", "rnn", "cnn"}

_AS_IS = {"c++", "c#", "next.js", "github", "gitlab", "graphql", "grpc",
          "wandb", "pytorch", "tensorflow", "fastapi", "scikit-learn",
          "sklearn", "langchain", "lightgbm", "catboost", "xgboost",
          "fastai", "pyspark", "mlflow", "kubeflow"}


def _display_skill(skill: str) -> str:
    """Return a display-friendly casing for a skill name."""
    low = skill.lower()
    if low in _UPPER:
        return skill.upper()
    if low in _AS_IS:
        return skill  # already correctly cased in the list
    return skill.title()

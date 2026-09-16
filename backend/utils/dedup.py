"""SHA-256 based deduplication for job listings."""
from __future__ import annotations

import hashlib
import logging

logger = logging.getLogger(__name__)


def generate_id(company: str, title: str) -> str:
    """Generate a stable 16-char hex ID from company+title pair."""
    key = f"{company.strip().lower()}|{title.strip().lower()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def deduplicate(jobs: list[dict]) -> list[dict]:
    """Remove duplicate jobs by company+title hash. Mutates each job dict to add 'id'."""
    seen: set[str] = set()
    unique: list[dict] = []
    dupes = 0

    for job in jobs:
        job_id = generate_id(job.get("company", ""), job.get("title", ""))
        if job_id not in seen:
            seen.add(job_id)
            job["id"] = job_id
            unique.append(job)
        else:
            dupes += 1

    logger.info(f"Dedup: {len(unique)} unique, {dupes} duplicates removed")
    return unique

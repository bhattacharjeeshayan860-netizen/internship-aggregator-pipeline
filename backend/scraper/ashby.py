"""Ashby ATS scraper — api.ashbyhq.com/posting-api/job-board/{slug}

All companies are fetched concurrently (up to MAX_CONCURRENT at once).
"""
from __future__ import annotations

import asyncio
import logging

from .base import BaseScraper

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 10

# Verified Ashby slugs — focus on companies known for internship programs
ASHBY_COMPANIES: list[str] = [
    # ── AI Labs (most active on Ashby) ────────────────────────────────────
    "mistral",
    "perplexity",
    "character",
    "runway",
    "pika",
    "elevenlabs",
    "cohere",
    "imbue",
    "suno",
    # ── MLOps / LLMOps ────────────────────────────────────────────────────
    "weights-biases",
    "replicate",
    "modal-labs",
    "anyscale",
    "bentoml",
    "braintrust",
    "baseten",
    "arize",
    # ── Dev Tools / Infra ──────────────────────────────────────────────────
    "temporal",
    "linear",
    "retool",
    "tinybird",
    "liveblocks",
    "airplane",
    "together-computer",
    # ── AI Research ────────────────────────────────────────────────────────
    "evidently-ai",
    "whylabs",
    "truera",
    # ── Singapore 🇸🇬 ─────────────────────────────────────────────────────
    "sea-group",
    # ── UK / Europe 🇬🇧🇪🇺 ────────────────────────────────────────────────
    "causaly",
]


class AshbyScraper(BaseScraper):
    NAME = "ashby"
    BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"

    async def fetch(self) -> list[dict]:
        sem = asyncio.Semaphore(MAX_CONCURRENT)

        async def fetch_one(slug: str) -> list[dict]:
            async with sem:
                try:
                    data = await self._get(self.BASE_URL.format(slug=slug))
                    raw: list[dict] = (
                        data.get("jobPostings", []) if isinstance(data, dict) else []
                    )
                    if raw:
                        logger.info(f"[ashby] {slug}: {len(raw)} jobs")
                    return [self._normalise(j, slug) for j in raw]
                except Exception as exc:
                    logger.warning(f"[ashby] {slug} exception: {exc}")
                    return []

        results = await asyncio.gather(*[fetch_one(s) for s in ASHBY_COMPANIES])
        jobs = [job for batch in results for job in batch]
        logger.info(f"[ashby] total: {len(jobs)} jobs from {len(ASHBY_COMPANIES)} targets")
        return jobs

    @staticmethod
    def _normalise(job: dict, company_slug: str) -> dict:
        location = job.get("location", "")
        if isinstance(location, dict):
            location = location.get("name", "")

        title = job.get("title", "")
        # Ashby sometimes stores employment type separately
        employment_type = job.get("employmentType", "") or job.get("type", "")
        if employment_type and employment_type.lower() not in title.lower():
            title = f"{title} - {employment_type}"

        return {
            "source": "ashby",
            "company": company_slug.replace("-", " ").title(),
            "title": title,
            "location": location or "",
            "apply_url": job.get("jobUrl") or job.get("externalLink", ""),
            "description": job.get("descriptionHtml") or job.get("description", ""),
            "posted_date": job.get("updatedAt", ""),
        }

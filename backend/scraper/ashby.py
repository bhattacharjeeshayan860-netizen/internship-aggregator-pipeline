"""Ashby ATS scraper — api.ashbyhq.com/posting-api/job-board/{slug}

All companies are fetched concurrently (up to MAX_CONCURRENT at once).
"""
from __future__ import annotations

import asyncio
import logging

from .base import BaseScraper

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 10

# Verified Ashby slugs
ASHBY_COMPANIES: list[str] = [
    # ── Cutting-edge AI Labs ───────────────────────────────────────────────
    "mistral",
    "perplexity",
    "imbue",
    "character",
    "runway",
    "together-computer",
    "modal-labs",
    "anyscale",
    "pika",
    "suno",
    "cohere",
    # ── MLOps / LLMOps ────────────────────────────────────────────────────
    "weights-biases",
    "evidently-ai",
    "whylabs",
    "bentoml",
    "truera",
    "arize",
    # ── Dev Tools / Infra ──────────────────────────────────────────────────
    "temporal",
    "buf",
    "turso",
    "tinybird",
    "airplane",
    "braintrust",
    "baseten",
    # ── Product / SaaS ─────────────────────────────────────────────────────
    "linear",
    "retool",
    "liveblocks",
    # ── UK / Europe 🇬🇧🇪🇺 ────────────────────────────────────────────────
    "causaly",
    "tractable",
    "synthesia",
    "wayve",
    # ── Singapore 🇸🇬 ─────────────────────────────────────────────────────
    "sea-group",
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

        return {
            "source": "ashby",
            "company": company_slug.replace("-", " ").title(),
            "title": job.get("title", ""),
            "location": location or "",
            "apply_url": job.get("jobUrl") or job.get("externalLink", ""),
            "description": job.get("descriptionHtml") or job.get("description", ""),
            "posted_date": job.get("updatedAt", ""),
        }

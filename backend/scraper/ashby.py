"""Ashby ATS scraper — api.ashbyhq.com/posting-api/job-board/{slug}

Ashby exposes a clean JSON endpoint per company that returns all active job postings.
This is common among newer AI-native startups (Mistral, Perplexity, Modal, etc.).
"""
from __future__ import annotations

import logging

from .base import BaseScraper

logger = logging.getLogger(__name__)

ASHBY_COMPANIES: list[str] = [
    # ── Cutting-edge AI Labs ──────────────────────────────────────────────────
    "mistral",
    "perplexity",
    "imbue",
    "character",
    "runway",
    "together-computer",
    "modal-labs",
    "anyscale",
    "fixie",
    "cohere",
    "krea",
    "pika",
    "suno",
    # ── MLOps / LLMOps ───────────────────────────────────────────────────────
    "weights-biases",
    "evidently-ai",
    "whylabs",
    "neptune",
    "bentoml",
    "truera",
    "arize",
    # ── Dev Tools / Infra ─────────────────────────────────────────────────────
    "temporal",
    "buf",
    "turso",
    "tinybird",
    "airplane",
    "braintrust",
    "baseten",
    # ── Product / SaaS ────────────────────────────────────────────────────────
    "linear",
    "retool",
    "liveblocks",
    "trigger",
    # ── Canada 🇨🇦 / APAC ───────────────────────────────────────────────────
    "d2l",
    "caseware",
    # ── UK / Europe 🇬🇧🇪🇺 ──────────────────────────────────────────────────
    "causaly",
    "tractable",
    "synthesia",
    "wayve",
    "deepmind",
    # ── Singapore 🇸🇬 ────────────────────────────────────────────────────────
    "sea-group",
]


class AshbyScraper(BaseScraper):
    NAME = "ashby"
    BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"

    async def fetch(self) -> list[dict]:
        jobs: list[dict] = []
        for slug in ASHBY_COMPANIES:
            try:
                data = await self._get(self.BASE_URL.format(slug=slug))
                raw_jobs: list[dict] = (
                    data.get("jobPostings", []) if isinstance(data, dict) else []
                )
                for job in raw_jobs:
                    jobs.append(self._normalise(job, slug))
                if raw_jobs:
                    logger.info(f"[ashby] {slug}: {len(raw_jobs)} jobs")
            except Exception as exc:
                logger.warning(f"[ashby] {slug} failed: {exc}")
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

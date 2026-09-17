"""Lever ATS scraper — api.lever.co/v0/postings/{slug}

All companies are fetched concurrently (up to MAX_CONCURRENT at once).
"""
from __future__ import annotations

import asyncio
import logging

from .base import BaseScraper

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 12

# Verified Lever slugs — focus on companies with known active internship programs
LEVER_COMPANIES: list[str] = [
    # ── Large Tech / Growth-stage (high intern probability) ────────────────
    "scale-ai",
    "anduril",
    "openai",          # OpenAI switched to Lever for some roles
    "notion",
    "figma",           # Figma is on both Greenhouse and Lever
    # ── Fintech ────────────────────────────────────────────────────────────
    "brex",
    "mercury",
    "ramp",
    "gusto",
    "carta",
    "pilot",
    "wealthsimple",
    # ── AI / ML ────────────────────────────────────────────────────────────
    "perplexity-ai",
    "covariant",
    "cohere",
    "kensho",
    "contextual-ai",
    # ── Data / Analytics ───────────────────────────────────────────────────
    "amplitude",
    "mixpanel",
    "posthog",
    "rudderstack",
    "hightouch",
    "census",
    # ── Developer Tools ────────────────────────────────────────────────────
    "vercel",
    "replit",
    "retool",
    "linear",
    "descript",
    "loom",
    "temporal",
    "railway",
    # ── UK / Europe ────────────────────────────────────────────────────────
    "monzo",
    "cleo",
    "tractable",
    "causaly",
    # ── Infrastructure ─────────────────────────────────────────────────────
    "grafana",
    "cockroachdb",
    "neon",
    "latticehq",
]


class LeverScraper(BaseScraper):
    NAME = "lever"
    BASE_URL = "https://api.lever.co/v0/postings/{slug}"

    async def fetch(self) -> list[dict]:
        sem = asyncio.Semaphore(MAX_CONCURRENT)

        async def fetch_one(slug: str) -> list[dict]:
            async with sem:
                try:
                    data = await self._get(
                        self.BASE_URL.format(slug=slug),
                        params={"mode": "json", "limit": 100},
                    )
                    raw: list[dict] = data if isinstance(data, list) else data.get("data", [])
                    if raw:
                        logger.info(f"[lever] {slug}: {len(raw)} jobs")
                    return [self._normalise(j, slug) for j in raw]
                except Exception as exc:
                    logger.warning(f"[lever] {slug} exception: {exc}")
                    return []

        results = await asyncio.gather(*[fetch_one(s) for s in LEVER_COMPANIES])
        jobs = [job for batch in results for job in batch]
        logger.info(f"[lever] total: {len(jobs)} jobs from {len(LEVER_COMPANIES)} targets")
        return jobs

    @staticmethod
    def _normalise(job: dict, company_slug: str) -> dict:
        categories = job.get("categories", {})
        title = job.get("text", "")
        commitment = categories.get("commitment", "")

        # Many companies post "Software Engineer" with commitment="Internship".
        # Fold commitment into title so the internship filter can detect it.
        if commitment and commitment.lower() not in title.lower():
            title = f"{title} - {commitment}"

        return {
            "source": "lever",
            "company": company_slug.replace("-", " ").title(),
            "title": title,
            "location": categories.get("location", ""),
            "apply_url": job.get("hostedUrl") or job.get("applyUrl", ""),
            "description": job.get("descriptionPlain") or job.get("description", ""),
            "posted_date": "",
            "commitment": commitment,
        }

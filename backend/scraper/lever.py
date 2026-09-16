"""Lever ATS scraper — api.lever.co/v0/postings/{slug}

Lever's public API returns a JSON array of job postings per company slug.
The ?mode=json param ensures a clean JSON response (not HTML).
"""
from __future__ import annotations

import logging

from .base import BaseScraper

logger = logging.getLogger(__name__)

LEVER_COMPANIES: list[str] = [
    # ── AI / ML ───────────────────────────────────────────────────────────────
    "perplexity-ai",
    "covariant",
    "synthesis-ai",
    "skild-ai",
    "imbue",
    "together-ai",
    "tidepool",
    "contextual-ai",
    "kensho",
    "primer",
    # ── Developer Tools ───────────────────────────────────────────────────────
    "vercel",
    "linear",
    "retool",
    "descript",
    "loom",
    "replit",
    "temporal",
    "buf",
    "railway",
    "turso",
    "prisma",
    "fauna",
    # ── Data / Analytics ──────────────────────────────────────────────────────
    "posthog",
    "rudderstack",
    "tinybird",
    "census",
    "hightouch",
    "metaplane",
    # ── Product / SaaS ────────────────────────────────────────────────────────
    "miro",
    "notion",
    "figma",
    "amplitude",
    "mixpanel",
    "latticehq",
    "lattice",
    "carta",
    # ── Fintech ───────────────────────────────────────────────────────────────
    "brex",
    "mercury",
    "ramp",
    "pilot",
    "gusto",
    "stripe",
    # ── Canada 🇨🇦 ──────────────────────────────────────────────────────────
    "cohere",
    "vector-institute",
    "properly",
    # ── UK / Europe 🇬🇧🇪🇺 ──────────────────────────────────────────────────
    "monzo",
    "wise",
    "cleo",
    "tractable",
    "causaly",
    # ── Infrastructure ────────────────────────────────────────────────────────
    "grafana",
    "neon",
    "planetscale",
    "cockroachdb",
]


class LeverScraper(BaseScraper):
    NAME = "lever"
    BASE_URL = "https://api.lever.co/v0/postings/{slug}"

    async def fetch(self) -> list[dict]:
        jobs: list[dict] = []
        for slug in LEVER_COMPANIES:
            try:
                data = await self._get(
                    self.BASE_URL.format(slug=slug),
                    params={"mode": "json", "limit": 100},
                )
                raw_jobs: list[dict] = data if isinstance(data, list) else data.get("data", [])
                for job in raw_jobs:
                    jobs.append(self._normalise(job, slug))
                if raw_jobs:
                    logger.info(f"[lever] {slug}: {len(raw_jobs)} jobs")
            except Exception as exc:
                logger.warning(f"[lever] {slug} failed: {exc}")
        return jobs

    @staticmethod
    def _normalise(job: dict, company_slug: str) -> dict:
        categories = job.get("categories", {})
        return {
            "source": "lever",
            "company": company_slug.replace("-", " ").title(),
            "title": job.get("text", ""),
            "location": categories.get("location", ""),
            "apply_url": job.get("hostedUrl") or job.get("applyUrl", ""),
            "description": job.get("descriptionPlain") or job.get("description", ""),
            "posted_date": "",
            "commitment": categories.get("commitment", ""),
        }

"""Greenhouse ATS scraper — boards-api.greenhouse.io/v1/boards/{slug}/jobs

All companies are fetched concurrently (up to MAX_CONCURRENT at once) using a
semaphore, reducing total scrape time from O(N * delay) → O(slowest request).
"""
from __future__ import annotations

import asyncio
import logging

from .base import BaseScraper

logger = logging.getLogger(__name__)

# Max simultaneous requests to Greenhouse — polite ceiling to avoid bursts
MAX_CONCURRENT = 12

# Verified Greenhouse slugs (companies confirmed to use boards-api.greenhouse.io)
GREENHOUSE_COMPANIES: list[str] = [
    # ── AI / ML Frontier Labs ──────────────────────────────────────────────
    "anthropic",
    "cohere",
    "scale",
    "weightsandbiases",
    "databricks",
    "huggingface",
    "stability",
    "adept",
    "inflection",
    # ── MLOps / Data Infra ─────────────────────────────────────────────────
    "dbtlabs",
    "starburst",
    "airbyte",
    "prefect",
    "astronomer",
    "lightdash",
    # ── Developer Tools / Cloud ────────────────────────────────────────────
    "hashicorp",
    "confluent",
    "datadog",
    "newrelic",
    "elastic",
    "mongodb",
    "cockroachlabs",
    # ── Product / SaaS ─────────────────────────────────────────────────────
    "notion",
    "airtable",
    "figma",
    "amplitude",
    "mixpanel",
    "segment",
    "braze",
    "klaviyo",
    "lattice",
    # ── Fintech ────────────────────────────────────────────────────────────
    "stripe",
    "brex",
    "ramp",
    "plaid",
    "robinhood",
    "coinbase",
    "mercury",
    # ── Canada 🇨🇦 ─────────────────────────────────────────────────────────
    "coveo",
    "hootsuite",
    "freshbooks",
    "wealthsimple",
    # ── UK / Europe 🇬🇧🇪🇺 ────────────────────────────────────────────────
    "monzo",
    "revolut",
    "graphcore",
    "tractable",
    "improbable",
    # ── Singapore / APAC 🇸🇬 ─────────────────────────────────────────────
    "grab",
    # ── Health / Bio-Tech ──────────────────────────────────────────────────
    "recursion",
    "tempus",
    "genentech",
]


class GreenhouseScraper(BaseScraper):
    NAME = "greenhouse"
    BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

    async def fetch(self) -> list[dict]:
        sem = asyncio.Semaphore(MAX_CONCURRENT)

        async def fetch_one(slug: str) -> list[dict]:
            async with sem:
                try:
                    data = await self._get(
                        self.BASE_URL.format(slug=slug),
                        params={"content": "true"},
                    )
                    raw: list[dict] = data.get("jobs", []) if isinstance(data, dict) else []
                    if raw:
                        logger.info(f"[greenhouse] {slug}: {len(raw)} jobs")
                    return [self._normalise(j, slug) for j in raw]
                except Exception as exc:
                    logger.warning(f"[greenhouse] {slug} exception: {exc}")
                    return []

        results = await asyncio.gather(*[fetch_one(s) for s in GREENHOUSE_COMPANIES])
        jobs = [job for batch in results for job in batch]
        logger.info(f"[greenhouse] total: {len(jobs)} jobs from {len(GREENHOUSE_COMPANIES)} targets")
        return jobs

    @staticmethod
    def _normalise(job: dict, company_slug: str) -> dict:
        location = job.get("location", {})
        loc_str = location.get("name", "") if isinstance(location, dict) else str(location or "")
        company = (
            job.get("company_name")
            or company_slug.replace("-", " ").replace("_", " ").title()
        )
        return {
            "source": "greenhouse",
            "company": company,
            "title": job.get("title", ""),
            "location": loc_str,
            "apply_url": job.get("absolute_url", ""),
            "description": job.get("content", ""),
            "posted_date": job.get("updated_at", ""),
        }

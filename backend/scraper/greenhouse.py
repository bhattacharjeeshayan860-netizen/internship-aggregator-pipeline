"""Greenhouse ATS scraper — boards-api.greenhouse.io/v1/boards/{slug}/jobs

Greenhouse exposes clean JSON feeds with full job content. Zero HTML parsing required.
The ?content=true param includes full job descriptions in the response.
"""
from __future__ import annotations

import logging

from .base import BaseScraper

logger = logging.getLogger(__name__)

# Curated slugs — heavily biased toward AI/ML + DS companies that actively hire interns.
# Greenhouse slugs are typically the lowercase company name with hyphens.
GREENHOUSE_COMPANIES: list[str] = [
    # ── AI / ML Frontier Labs ─────────────────────────────────────────────────
    "anthropic",
    "cohere",
    "scale",
    "weightsandbiases",
    "databricks",
    "huggingface",
    "stability",
    "adept",
    "inflection",
    "runway",
    "alephalpha",
    # ── MLOps / Data Infra ────────────────────────────────────────────────────
    "dbtlabs",
    "starburst",
    "airbyte",
    "prefect",
    "great-expectations",
    "astronomer",
    "lightdash",
    # ── Developer Tools / Cloud ───────────────────────────────────────────────
    "hashicorp",
    "confluent",
    "datadog",
    "newrelic",
    "grafana",
    "elastic",
    "mongodb",
    "cockroachlabs",
    "supabase",
    "planetscale",
    # ── Product / SaaS ────────────────────────────────────────────────────────
    "notion",
    "airtable",
    "figma",
    "canva",
    "miro",
    "amplitude",
    "mixpanel",
    "segment",
    "braze",
    "klaviyo",
    # ── Fintech ───────────────────────────────────────────────────────────────
    "stripe",
    "brex",
    "ramp",
    "plaid",
    "robinhood",
    "coinbase",
    "mercury",
    # ── Canada 🇨🇦 ──────────────────────────────────────────────────────────
    "coveo",
    "d2l",
    "hootsuite",
    "freshbooks",
    "wealthsimple",
    # ── UK / Europe 🇬🇧🇪🇺 ──────────────────────────────────────────────────
    "monzo",
    "revolut",
    "graphcore",
    "tractable",
    "improbable",
    # ── Singapore / APAC 🇸🇬 ────────────────────────────────────────────────
    "grab",
    "sea",
    "govtech-singapore",
    # ── Health / Bio-Tech ─────────────────────────────────────────────────────
    "recursion",
    "insitro",
    "tempus",
    "genentech",
]


class GreenhouseScraper(BaseScraper):
    NAME = "greenhouse"
    BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

    async def fetch(self) -> list[dict]:
        jobs: list[dict] = []
        for slug in GREENHOUSE_COMPANIES:
            try:
                data = await self._get(
                    self.BASE_URL.format(slug=slug),
                    params={"content": "true"},
                )
                raw_jobs: list[dict] = data.get("jobs", []) if isinstance(data, dict) else []
                for job in raw_jobs:
                    jobs.append(self._normalise(job, slug))
                if raw_jobs:
                    logger.info(f"[greenhouse] {slug}: {len(raw_jobs)} jobs")
            except Exception as exc:
                logger.warning(f"[greenhouse] {slug} failed: {exc}")
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

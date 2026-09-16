"""Pydantic models for the Internship Aggregator API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class JobListing(BaseModel):
    id: str
    company: str
    title: str
    location: str
    work_mode: str  # "Remote" | "Hybrid" | "On-site"
    tech_score: int  # 0–100
    matched_keywords: list[str]
    stipend_estimate: str  # e.g. "~$25/hr" or "Not specified"
    apply_url: str
    source: str  # "greenhouse" | "lever" | "ashby"
    posted_date: Optional[str] = None

    @field_validator("tech_score")
    @classmethod
    def clamp_score(cls, v: int) -> int:
        return max(0, min(100, v))


class ScrapeResult(BaseModel):
    jobs: list[JobListing]
    total: int
    scraped_at: datetime
    cache_hit: bool = False

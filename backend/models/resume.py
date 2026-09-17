"""Pydantic models for resume processing."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class CandidateProfile(BaseModel):
    """Structured candidate profile extracted from a resume PDF."""

    skills: list[str]                   # e.g. ["Python", "SQL", "Docker"]
    roles: list[str]                    # e.g. ["Data Scientist", "ML Engineer"]
    education: list[str]                # e.g. ["B.Tech Computer Science"]
    years_of_experience: Optional[int] = None
    text_length: int = 0                # chars extracted — for diagnostics, never the raw text

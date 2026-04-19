from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Dict, List


class ArtifactType(str, Enum):
    RESUME_BULLETS = "resume_bullets"
    COVER_LETTER = "cover_letter"
    OUTREACH_EMAIL = "outreach_email"
    INTERVIEW_PREP = "interview_prep"


class PlanStatus(str, Enum):
    PLANNED = "planned"
    APPLIED = "applied"
    SKIPPED = "skipped"
    IN_PROGRESS = "in_progress"


@dataclass(slots=True)
class UserProfile:
    full_name: str
    email: str
    target_roles: List[str]
    skills: List[str]
    experience_summary: str = ""
    location_preference: str = ""


@dataclass(slots=True)
class JobPosting:
    source: str
    title: str
    company: str
    location: str
    url: str
    description: str
    tags: List[str] = field(default_factory=list)
    published_at: str = ""


@dataclass(slots=True)
class RankedJob:
    posting: JobPosting
    score: float
    matched_skills: List[str]
    missing_skills: List[str] = field(default_factory=list)
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    priority_label: str = ""
    reasoning: str = ""


@dataclass(slots=True)
class GeneratedArtifact:
    job_url: str
    artifact_type: ArtifactType
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class PipelineResult:
    fetched_count: int
    ranked_count: int
    top_jobs: List[RankedJob]
    run_id: int


@dataclass(slots=True)
class ApplicationPlanItem:
    id: int
    job_url: str
    title: str
    company: str
    score: float
    priority_label: str
    target_date: str
    status: PlanStatus
    notes: str = ""

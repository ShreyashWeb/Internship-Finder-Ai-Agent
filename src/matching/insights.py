from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import List

from src.core.models import RankedJob, UserProfile


@dataclass(slots=True)
class MatchInsights:
    average_score: float
    high_intent_count: int
    top_missing_skills: List[str]
    weekly_action_plan: List[str]



def generate_insights(profile: UserProfile, ranked_jobs: List[RankedJob]) -> MatchInsights:
    if not ranked_jobs:
        return MatchInsights(
            average_score=0.0,
            high_intent_count=0,
            top_missing_skills=[],
            weekly_action_plan=["Run a new search cycle after updating profile and skills."],
        )

    avg_score = sum(job.score for job in ranked_jobs) / len(ranked_jobs)
    high_intent_count = sum(1 for job in ranked_jobs if job.priority_label == "High Intent Apply")

    missing_counter: Counter[str] = Counter()
    for job in ranked_jobs[:20]:
        missing_counter.update(job.missing_skills[:5])

    top_missing = [skill for skill, _ in missing_counter.most_common(5)]
    plan = _build_weekly_plan(profile, top_missing)

    return MatchInsights(
        average_score=round(avg_score, 3),
        high_intent_count=high_intent_count,
        top_missing_skills=top_missing,
        weekly_action_plan=plan,
    )



def _build_weekly_plan(profile: UserProfile, top_missing: List[str]) -> List[str]:
    role_focus = ", ".join(profile.target_roles[:2]) or "internship roles"
    if not top_missing:
        return [
            f"Day 1-2: Apply to top 5 {role_focus} postings with tailored resumes.",
            "Day 3-4: Build one portfolio project narrative aligned to target roles.",
            "Day 5-7: Do 3 mock interviews and refine outreach emails.",
        ]

    focus = ", ".join(top_missing[:3])
    return [
        f"Day 1: Close top skill gap in {focus} with 2 focused study blocks.",
        "Day 2-3: Build a mini project proving these skills and push to GitHub.",
        "Day 4: Rewrite resume bullets to highlight project outcomes and metrics.",
        "Day 5: Apply to top 5 strong-match roles and send outreach emails.",
        "Day 6-7: Practice interview stories based on your new project and applications.",
    ]

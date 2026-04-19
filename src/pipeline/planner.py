from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import List

from src.core.models import ApplicationPlanItem, PlanStatus, RankedJob


class ApplicationPlanner:
    def build_plan(self, ranked_jobs: List[RankedJob], days: int = 7, per_day: int = 3) -> List[ApplicationPlanItem]:
        if days <= 0 or per_day <= 0:
            raise ValueError("days and per_day must be positive")

        today = datetime.now(UTC).date()
        capacity = days * per_day
        prioritized = sorted(ranked_jobs, key=self._priority_score, reverse=True)[:capacity]

        plan: List[ApplicationPlanItem] = []
        for index, job in enumerate(prioritized):
            day_offset = index // per_day
            target_date = (today + timedelta(days=day_offset)).isoformat()
            plan.append(
                ApplicationPlanItem(
                    id=0,
                    job_url=job.posting.url,
                    title=job.posting.title,
                    company=job.posting.company,
                    score=job.score,
                    priority_label=job.priority_label,
                    target_date=target_date,
                    status=PlanStatus.PLANNED,
                    notes=job.reasoning,
                )
            )
        return plan

    def _priority_score(self, ranked: RankedJob) -> float:
        urgency_boost = 0.0
        title = ranked.posting.title.lower()
        if "urgent" in title or "immediate" in title:
            urgency_boost = 0.08
        return ranked.score + urgency_boost

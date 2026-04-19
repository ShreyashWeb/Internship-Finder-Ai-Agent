from src.core.models import JobPosting, RankedJob
from src.pipeline.planner import ApplicationPlanner


def test_planner_builds_daily_capacity_plan() -> None:
    planner = ApplicationPlanner()
    ranked = [
        RankedJob(
            posting=JobPosting(
                source="x",
                title=f"Intern {idx}",
                company="A",
                location="Remote",
                url=f"https://example.com/{idx}",
                description="python",
            ),
            score=0.9 - (idx * 0.05),
            matched_skills=["python"],
            priority_label="Strong Match",
            reasoning="fit",
        )
        for idx in range(10)
    ]

    plan = planner.build_plan(ranked, days=2, per_day=3)
    assert len(plan) == 6
    assert plan[0].target_date <= plan[-1].target_date

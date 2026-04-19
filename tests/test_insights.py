from src.core.models import JobPosting, RankedJob, UserProfile
from src.matching.insights import generate_insights


def test_generate_insights_returns_actionable_plan() -> None:
    profile = UserProfile(
        full_name="Test",
        email="test@example.com",
        target_roles=["Software Engineer Intern"],
        skills=["python", "sql"],
    )
    ranked = [
        RankedJob(
            posting=JobPosting(
                source="x",
                title="Software Engineer Intern",
                company="A",
                location="Remote",
                url="https://example.com/1",
                description="python, react",
            ),
            score=0.8,
            matched_skills=["python"],
            missing_skills=["react"],
            priority_label="High Intent Apply",
        ),
        RankedJob(
            posting=JobPosting(
                source="x",
                title="Backend Intern",
                company="B",
                location="Remote",
                url="https://example.com/2",
                description="sql, docker",
            ),
            score=0.6,
            matched_skills=["sql"],
            missing_skills=["docker"],
            priority_label="Strong Match",
        ),
    ]

    insights = generate_insights(profile, ranked)
    assert insights.average_score > 0
    assert insights.high_intent_count == 1
    assert len(insights.weekly_action_plan) >= 3

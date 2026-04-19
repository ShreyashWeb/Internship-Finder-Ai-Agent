from src.core.models import JobPosting, UserProfile
from src.matching.scorer import JobScorer


def test_job_scorer_ranks_matching_jobs_higher() -> None:
    profile = UserProfile(
        full_name="Test User",
        email="test@example.com",
        target_roles=["Software Engineer Intern"],
        skills=["python", "sql", "apis"],
    )
    postings = [
        JobPosting(
            source="x",
            title="Software Engineer Intern",
            company="A",
            location="Remote",
            url="https://example.com/1",
            description="Need python and sql skills for backend apis",
            tags=["python"],
        ),
        JobPosting(
            source="x",
            title="Marketing Intern",
            company="B",
            location="Remote",
            url="https://example.com/2",
            description="social media and branding",
            tags=["marketing"],
        ),
    ]

    ranked = JobScorer(threshold=0.0).rank(profile, postings)
    assert ranked[0].posting.url == "https://example.com/1"
    assert ranked[0].score > ranked[1].score

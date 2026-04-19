from src.core.models import ArtifactType, JobPosting, UserProfile
from src.generation.artifact_service import ArtifactService
from src.generation.openai_client import OpenAITextClient


def test_generation_fallback_without_api_key() -> None:
    client = OpenAITextClient(api_key="", model="gpt-4.1-mini")
    service = ArtifactService(client)
    profile = UserProfile(
        full_name="Test User",
        email="test@example.com",
        target_roles=["Software Engineer Intern"],
        skills=["python", "sql"],
    )
    posting = JobPosting(
        source="x",
        title="Software Engineer Intern",
        company="Example",
        location="Remote",
        url="https://example.com/job",
        description="python and sql",
    )

    artifact = service.generate(profile, posting, ArtifactType.COVER_LETTER)
    assert "Example" in artifact.content

from src.core.config import Settings
from src.core.models import UserProfile
from src.data.db import get_connection, init_db
from src.data.repositories import JobRepository, ProfileRepository, RunRepository
from src.pipeline.run_pipeline import InternshipHunterPipeline


class StubCollectorPipeline(InternshipHunterPipeline):
    def run(self, profile=None):
        return super().run(profile)


def test_pipeline_requires_profile(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    settings = Settings(
        openai_api_key="",
        openai_model="gpt-4.1-mini",
        database_path=db_path,
        export_dir=tmp_path,
        match_threshold=0.1,
        max_results=10,
        schedule_time="09:00",
        rss_feeds=[],
        remotive_category="software-dev",
        remotive_limit=1,
    )

    conn = get_connection(settings.database_path)
    init_db(conn)

    pipeline = InternshipHunterPipeline(
        settings,
        profile_repo=ProfileRepository(conn),
        job_repo=JobRepository(conn),
        run_repo=RunRepository(conn),
    )

    try:
        pipeline.run()
    except ValueError as exc:
        assert "No profile found" in str(exc)
    else:
        raise AssertionError("Expected ValueError when profile is missing")


def test_profile_round_trip(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    conn = get_connection(db_path)
    init_db(conn)
    repo = ProfileRepository(conn)

    profile = UserProfile(
        full_name="A",
        email="a@example.com",
        target_roles=["Data Intern"],
        skills=["python"],
    )
    repo.upsert(profile)
    loaded = repo.get()

    assert loaded is not None
    assert loaded.full_name == "A"

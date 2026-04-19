from __future__ import annotations

import sqlite3

from src.core.config import Settings, get_settings
from src.data.db import get_connection, init_db
from src.data.repositories import (
    ApplicationPlanRepository,
    ArtifactRepository,
    JobRepository,
    ProfileRepository,
    RunRepository,
)
from src.generation.artifact_service import ArtifactService
from src.generation.openai_client import OpenAITextClient
from src.pipeline.run_pipeline import InternshipHunterPipeline


class AppContainer:
    def __init__(self, settings: Settings, conn: sqlite3.Connection) -> None:
        self.settings = settings
        self.conn = conn

        self.profile_repo = ProfileRepository(conn)
        self.job_repo = JobRepository(conn)
        self.run_repo = RunRepository(conn)
        self.artifact_repo = ArtifactRepository(conn)
        self.plan_repo = ApplicationPlanRepository(conn)

        self.artifact_service = ArtifactService(
            OpenAITextClient(api_key=settings.openai_api_key, model=settings.openai_model)
        )
        self.pipeline = InternshipHunterPipeline(
            settings=settings,
            profile_repo=self.profile_repo,
            job_repo=self.job_repo,
            run_repo=self.run_repo,
        )



def build_container() -> AppContainer:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)
    return AppContainer(settings=settings, conn=conn)

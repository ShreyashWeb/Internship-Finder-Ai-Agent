from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Iterable, List, Optional

from src.core.models import (
    ApplicationPlanItem,
    ArtifactType,
    GeneratedArtifact,
    JobPosting,
    PlanStatus,
    RankedJob,
    UserProfile,
)


class ProfileRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def upsert(self, profile: UserProfile) -> None:
        payload = {
            "full_name": profile.full_name,
            "email": profile.email,
            "target_roles": json.dumps(profile.target_roles),
            "skills": json.dumps(profile.skills),
            "experience_summary": profile.experience_summary,
            "location_preference": profile.location_preference,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        self.conn.execute(
            """
            INSERT INTO user_profile (
                id, full_name, email, target_roles, skills,
                experience_summary, location_preference, updated_at
            )
            VALUES (1, :full_name, :email, :target_roles, :skills,
                    :experience_summary, :location_preference, :updated_at)
            ON CONFLICT(id) DO UPDATE SET
                full_name=excluded.full_name,
                email=excluded.email,
                target_roles=excluded.target_roles,
                skills=excluded.skills,
                experience_summary=excluded.experience_summary,
                location_preference=excluded.location_preference,
                updated_at=excluded.updated_at
            """,
            payload,
        )
        self.conn.commit()

    def get(self) -> Optional[UserProfile]:
        row = self.conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
        if not row:
            return None
        return UserProfile(
            full_name=row["full_name"],
            email=row["email"],
            target_roles=json.loads(row["target_roles"]),
            skills=json.loads(row["skills"]),
            experience_summary=row["experience_summary"],
            location_preference=row["location_preference"],
        )


class JobRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save_many(self, postings: Iterable[JobPosting]) -> int:
        inserted = 0
        for posting in postings:
            cur = self.conn.execute(
                """
                INSERT OR IGNORE INTO jobs (
                    source, title, company, location, url,
                    description, tags, published_at, fetched_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    posting.source,
                    posting.title,
                    posting.company,
                    posting.location,
                    posting.url,
                    posting.description,
                    json.dumps(posting.tags),
                    posting.published_at,
                    datetime.now(UTC).isoformat(),
                ),
            )
            inserted += cur.rowcount
        self.conn.commit()
        return inserted

    def list_recent(self, limit: int) -> List[JobPosting]:
        rows = self.conn.execute(
            """
            SELECT source, title, company, location, url, description, tags, published_at
            FROM jobs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            JobPosting(
                source=row["source"],
                title=row["title"],
                company=row["company"],
                location=row["location"],
                url=row["url"],
                description=row["description"],
                tags=json.loads(row["tags"]),
                published_at=row["published_at"],
            )
            for row in rows
        ]

    def get_job_id_by_url(self, url: str) -> Optional[int]:
        row = self.conn.execute("SELECT id FROM jobs WHERE url = ?", (url,)).fetchone()
        return int(row["id"]) if row else None


class RunRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def start(self) -> int:
        cur = self.conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, ?)",
            (datetime.now(UTC).isoformat(), "running"),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def finish(self, run_id: int, fetched_count: int, ranked_count: int) -> None:
        self.conn.execute(
            """
            UPDATE runs
            SET finished_at = ?, fetched_count = ?, ranked_count = ?, status = ?
            WHERE id = ?
            """,
            (datetime.now(UTC).isoformat(), fetched_count, ranked_count, "success", run_id),
        )
        self.conn.commit()

    def fail(self, run_id: int, message: str) -> None:
        self.conn.execute(
            """
            UPDATE runs
            SET finished_at = ?, status = ?, error_message = ?
            WHERE id = ?
            """,
            (datetime.now(UTC).isoformat(), "failed", message[:1000], run_id),
        )
        self.conn.commit()

    def save_ranked_jobs(self, run_id: int, ranked_jobs: List[RankedJob], job_repo: JobRepository) -> None:
        for ranked in ranked_jobs:
            job_id = job_repo.get_job_id_by_url(ranked.posting.url)
            if job_id is None:
                continue
            self.conn.execute(
                """
                INSERT OR REPLACE INTO ranked_jobs (run_id, job_id, score, matched_skills)
                VALUES (?, ?, ?, ?)
                """,
                (run_id, job_id, ranked.score, json.dumps(ranked.matched_skills)),
            )
        self.conn.commit()


class ArtifactRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save(self, artifact: GeneratedArtifact) -> None:
        self.conn.execute(
            """
            INSERT INTO artifacts (job_url, artifact_type, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                artifact.job_url,
                artifact.artifact_type.value,
                artifact.content,
                artifact.created_at.isoformat(),
            ),
        )
        self.conn.commit()

    def list_for_job(self, job_url: str) -> List[GeneratedArtifact]:
        rows = self.conn.execute(
            "SELECT * FROM artifacts WHERE job_url = ? ORDER BY id DESC", (job_url,)
        ).fetchall()
        return [
            GeneratedArtifact(
                job_url=row["job_url"],
                artifact_type=ArtifactType(row["artifact_type"]),
                content=row["content"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]


class ApplicationPlanRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def replace_plan(self, items: List[ApplicationPlanItem]) -> None:
        now = datetime.now(UTC).isoformat()
        self.conn.execute("DELETE FROM application_plan")
        for item in items:
            self.conn.execute(
                """
                INSERT INTO application_plan (
                    job_url, title, company, score, priority_label,
                    target_date, status, notes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.job_url,
                    item.title,
                    item.company,
                    item.score,
                    item.priority_label,
                    item.target_date,
                    item.status.value,
                    item.notes,
                    now,
                    now,
                ),
            )
        self.conn.commit()

    def list_by_date(self, target_date: str) -> List[ApplicationPlanItem]:
        rows = self.conn.execute(
            """
            SELECT * FROM application_plan
            WHERE target_date = ?
            ORDER BY score DESC
            """,
            (target_date,),
        ).fetchall()
        return [self._map_row(row) for row in rows]

    def list_upcoming(self, limit: int = 30) -> List[ApplicationPlanItem]:
        rows = self.conn.execute(
            """
            SELECT * FROM application_plan
            ORDER BY target_date ASC, score DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._map_row(row) for row in rows]

    def update_status(self, item_id: int, status: PlanStatus, notes: str = "") -> None:
        self.conn.execute(
            """
            UPDATE application_plan
            SET status = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (status.value, notes, datetime.now(UTC).isoformat(), item_id),
        )
        self.conn.commit()

    def _map_row(self, row: sqlite3.Row) -> ApplicationPlanItem:
        return ApplicationPlanItem(
            id=int(row["id"]),
            job_url=row["job_url"],
            title=row["title"],
            company=row["company"],
            score=float(row["score"]),
            priority_label=row["priority_label"],
            target_date=row["target_date"],
            status=PlanStatus(row["status"]),
            notes=row["notes"],
        )

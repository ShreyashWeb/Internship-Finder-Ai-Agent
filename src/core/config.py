from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
    openai_api_key: str
    openai_model: str
    database_path: Path
    export_dir: Path
    match_threshold: float
    max_results: int
    schedule_time: str
    rss_feeds: List[str]
    remotive_category: str
    remotive_limit: int



def _parse_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]



def get_settings() -> Settings:
    default_db = "/tmp/internship_hunter.db" if os.getenv("VERCEL") else "data/internship_hunter.db"
    default_exports = "/tmp/exports" if os.getenv("VERCEL") else "data/exports"

    database_path = Path(os.getenv("DATABASE_PATH", default_db))
    export_dir = Path(os.getenv("EXPORT_DIR", default_exports))

    database_path.parent.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        database_path=database_path,
        export_dir=export_dir,
        match_threshold=float(os.getenv("MATCH_THRESHOLD", "0.20")),
        max_results=int(os.getenv("MAX_RESULTS", "50")),
        schedule_time=os.getenv("SCHEDULE_TIME", "09:00"),
        rss_feeds=_parse_csv(
            os.getenv(
                "RSS_FEEDS",
                "https://weworkremotely.com/remote-jobs.rss,https://remoteok.com/remote-dev-jobs.rss",
            )
        ),
        remotive_category=os.getenv("REMOTIVE_CATEGORY", "software-dev"),
        remotive_limit=int(os.getenv("REMOTIVE_LIMIT", "50")),
    )

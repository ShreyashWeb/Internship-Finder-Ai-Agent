from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler

from src.pipeline.run_pipeline import InternshipHunterPipeline


class DailyScheduler:
    def __init__(self, pipeline: InternshipHunterPipeline, daily_time: str) -> None:
        self.pipeline = pipeline
        self.daily_time = daily_time

    def start(self) -> None:
        hour, minute = self._parse_time(self.daily_time)
        scheduler = BlockingScheduler()
        scheduler.add_job(self.pipeline.run, "cron", hour=hour, minute=minute)
        scheduler.start()

    @staticmethod
    def _parse_time(value: str) -> tuple[int, int]:
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError("SCHEDULE_TIME must be HH:MM")
        return int(parts[0]), int(parts[1])

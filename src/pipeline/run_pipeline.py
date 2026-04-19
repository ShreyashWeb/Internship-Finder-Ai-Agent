from __future__ import annotations

from typing import List

from src.core.config import Settings
from src.core.models import PipelineResult, RankedJob, UserProfile
from src.data.repositories import JobRepository, ProfileRepository, RunRepository
from src.matching.scorer import JobScorer
from src.sources.collector import SourceCollector
from src.sources.remotive_api import RemotiveJobSource
from src.sources.rss_feeds import RSSJobSource


class InternshipHunterPipeline:
    def __init__(
        self,
        settings: Settings,
        profile_repo: ProfileRepository,
        job_repo: JobRepository,
        run_repo: RunRepository,
    ) -> None:
        self.settings = settings
        self.profile_repo = profile_repo
        self.job_repo = job_repo
        self.run_repo = run_repo

    def run(self, profile: UserProfile | None = None) -> PipelineResult:
        active_profile = profile or self.profile_repo.get()
        if not active_profile:
            raise ValueError("No profile found. Create a profile first.")

        run_id = self.run_repo.start()
        try:
            collector = SourceCollector(
                [
                    RemotiveJobSource(
                        category=self.settings.remotive_category,
                        limit=self.settings.remotive_limit,
                    ),
                    RSSJobSource(self.settings.rss_feeds),
                ]
            )
            postings = collector.collect()
            self.job_repo.save_many(postings)

            recent = self.job_repo.list_recent(self.settings.max_results)
            ranked = JobScorer(threshold=self.settings.match_threshold).rank(active_profile, recent)
            top_ranked = ranked[: self.settings.max_results]

            self.run_repo.save_ranked_jobs(run_id, top_ranked, self.job_repo)
            self.run_repo.finish(run_id, fetched_count=len(postings), ranked_count=len(top_ranked))

            return PipelineResult(
                fetched_count=len(postings),
                ranked_count=len(top_ranked),
                top_jobs=top_ranked,
                run_id=run_id,
            )
        except Exception as exc:
            self.run_repo.fail(run_id, str(exc))
            raise



def format_ranked_jobs(ranked: List[RankedJob]) -> str:
    lines = []
    for index, item in enumerate(ranked, start=1):
        lines.append(
            f"{index}. {item.posting.title} | {item.posting.company} | score={item.score:.2f} | {item.priority_label or 'Match'} | {item.posting.url}"
        )
    return "\n".join(lines)

from __future__ import annotations

from typing import List

from src.core.models import JobPosting
from src.sources.base import JobSource


class SourceCollector:
    def __init__(self, sources: List[JobSource]) -> None:
        self.sources = sources

    def collect(self) -> List[JobPosting]:
        postings: List[JobPosting] = []
        seen_urls: set[str] = set()

        for source in self.sources:
            try:
                batch = source.fetch()
            except Exception:
                continue

            for posting in batch:
                if posting.url in seen_urls:
                    continue
                seen_urls.add(posting.url)
                postings.append(posting)

        return postings

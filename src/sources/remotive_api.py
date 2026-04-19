from __future__ import annotations

from typing import List

import requests

from src.core.models import JobPosting
from src.sources.base import JobSource


class RemotiveJobSource(JobSource):
    BASE_URL = "https://remotive.com/api/remote-jobs"

    def __init__(self, category: str = "software-dev", limit: int = 50) -> None:
        self.name = "remotive"
        self.category = category
        self.limit = limit

    def fetch(self) -> List[JobPosting]:
        response = requests.get(
            self.BASE_URL,
            params={"category": self.category, "limit": self.limit},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()

        postings: List[JobPosting] = []
        for item in payload.get("jobs", []):
            postings.append(
                JobPosting(
                    source=self.name,
                    title=item.get("title", ""),
                    company=item.get("company_name", "Unknown"),
                    location=item.get("candidate_required_location", "Remote"),
                    url=item.get("url", ""),
                    description=item.get("description", ""),
                    tags=item.get("tags", []),
                    published_at=item.get("publication_date", ""),
                )
            )

        return [p for p in postings if p.title and p.url]

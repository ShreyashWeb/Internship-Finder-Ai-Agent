from __future__ import annotations

from typing import List

import feedparser

from src.core.models import JobPosting
from src.sources.base import JobSource


class RSSJobSource(JobSource):
    def __init__(self, feed_urls: List[str]) -> None:
        self.name = "rss"
        self.feed_urls = feed_urls

    def fetch(self) -> List[JobPosting]:
        postings: List[JobPosting] = []
        for url in self.feed_urls:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = getattr(entry, "title", "")
                description = getattr(entry, "summary", "")
                link = getattr(entry, "link", "")
                if not title or not link:
                    continue
                postings.append(
                    JobPosting(
                        source=f"rss:{url}",
                        title=title,
                        company=_extract_company(title),
                        location=_extract_location(description),
                        url=link,
                        description=description,
                        tags=[],
                        published_at=getattr(entry, "published", ""),
                    )
                )
        return postings



def _extract_company(title: str) -> str:
    if " at " in title.lower():
        parts = title.split(" at ")
        if len(parts) > 1:
            return parts[-1].strip()
    return "Unknown"



def _extract_location(description: str) -> str:
    lowered = description.lower()
    if "remote" in lowered:
        return "Remote"
    return "Not specified"

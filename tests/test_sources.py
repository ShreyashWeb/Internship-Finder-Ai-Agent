from src.sources.collector import SourceCollector


class DummySource:
    def __init__(self, postings):
        self.postings = postings

    def fetch(self):
        return self.postings


def test_collector_deduplicates_by_url() -> None:
    posting = type("Job", (), {"url": "https://example.com/1"})()
    collector = SourceCollector([DummySource([posting]), DummySource([posting])])
    result = collector.collect()
    assert len(result) == 1

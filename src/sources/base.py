from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.core.models import JobPosting


class JobSource(ABC):
    name: str

    @abstractmethod
    def fetch(self) -> List[JobPosting]:
        raise NotImplementedError

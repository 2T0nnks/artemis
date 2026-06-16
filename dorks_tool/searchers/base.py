from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    engine: str


class BaseSearcher(ABC):
    name: str = ""
    slug: str = ""
    requires_key: bool = False

    @abstractmethod
    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        ...

    def is_available(self) -> bool:
        return True

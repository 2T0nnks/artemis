from typing import List
from .base import BaseSearcher, SearchResult
from ._bing_utils import bing_search


class BingSearcher(BaseSearcher):
    name = "Bing"
    slug = "bing"
    requires_key = False

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        return bing_search(
            query, max_results, self.name,
            params={"q": query, "setlang": "en", "cc": "US"},
        )

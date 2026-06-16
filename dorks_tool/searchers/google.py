from typing import List
from .base import BaseSearcher, SearchResult
from ._bing_utils import bing_search


class BingGlobalSearcher(BaseSearcher):
    name = "Bing (Global)"
    slug = "google"
    requires_key = False

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        return bing_search(
            query, max_results, self.name,
            params={"q": query, "mkt": "en-GB", "cc": "GB"},
            extra_headers={"Accept-Language": "en-GB,en;q=0.5"},
        )

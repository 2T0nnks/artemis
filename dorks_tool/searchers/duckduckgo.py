from typing import List
from .base import BaseSearcher, SearchResult


class DuckDuckGoSearcher(BaseSearcher):
    name = "DuckDuckGo"
    slug = "ddg"
    requires_key = False

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        try:
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results, backend='html'):
                    results.append(SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", ""),
                        engine=self.name,
                    ))
            return results
        except Exception:
            return []

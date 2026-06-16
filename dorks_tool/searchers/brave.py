import os
from typing import List
from .base import BaseSearcher, SearchResult
from ..http_client import request_with_retry


class BraveSearcher(BaseSearcher):
    name = "Brave"
    slug = "brave"
    requires_key = True

    def is_available(self) -> bool:
        return bool(os.environ.get("BRAVE_API_KEY", "").strip())

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        api_key = os.environ.get("BRAVE_API_KEY", "").strip()
        if not api_key:
            return []
        results = []
        try:
            resp = request_with_retry(
                "GET",
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": min(max_results, 20)},
                extra_headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": api_key,
                },
            )
            if resp is None:
                return results
            data = resp.json()
            for item in data.get("web", {}).get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    engine=self.name,
                ))
        except Exception:
            pass
        return results

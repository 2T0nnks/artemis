import random
import logging
from typing import List
from .base import BaseSearcher, SearchResult
from ..http_client import request_with_retry

logger = logging.getLogger(__name__)

# Public SearXNG instances — shuffled each search for load distribution
_INSTANCES = [
    "https://searx.be",
    "https://search.bus-hit.me",
    "https://searxng.world",
    "https://searx.tiekoetter.com",
    "https://search.sapti.me",
    "https://searx.prvcy.eu",
    "https://searx.fmac.xyz",
]


class SearXSearcher(BaseSearcher):
    """SearXNG meta-search — aggregates 70+ engines via public instances."""
    name = "SearX"
    slug = "searx"
    requires_key = False

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        results = []
        instances = _INSTANCES.copy()
        random.shuffle(instances)
        for base in instances:
            try:
                resp = request_with_retry(
                    "GET",
                    f"{base}/search",
                    params={"q": query, "format": "json", "categories": "general"},
                    extra_headers={"Referer": base + "/"},
                    timeout=8,
                )
                if resp is None or resp.status_code != 200:
                    logger.debug("[SearX] %s returned %s", base, getattr(resp, 'status_code', None))
                    continue
                data = resp.json()
                logger.debug("[SearX] %s returned %d results", base, len(data.get('results', [])))
                for item in data.get("results", [])[:max_results]:
                    url = item.get("url", "")
                    if not url or not url.startswith("http"):
                        continue
                    results.append(SearchResult(
                        title=item.get("title", ""),
                        url=url,
                        snippet=item.get("content", ""),
                        engine=self.name,
                    ))
                if results:
                    return results
            except Exception as exc:
                logger.debug("[SearX] %s exception: %s", base, exc)
                continue
        return results

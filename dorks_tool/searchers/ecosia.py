import logging
from bs4 import BeautifulSoup
from typing import List
from .base import BaseSearcher, SearchResult
from ..http_client import request_with_retry

logger = logging.getLogger(__name__)


class EcosiaSearcher(BaseSearcher):
    """Ecosia — eco-friendly search with own index layer on top of Bing."""
    name = "Ecosia"
    slug = "ecosia"
    requires_key = False

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        results = []
        try:
            resp = request_with_retry(
                "GET",
                "https://www.ecosia.org/search",
                params={"q": query, "addon": "opensearch"},
                extra_headers={"Referer": "https://www.ecosia.org/"},
            )
            if resp is None or resp.status_code >= 400:
                logger.debug("[Ecosia] bad response: %s", getattr(resp, 'status_code', None))
                return results
            soup = BeautifulSoup(resp.text, "lxml")
            candidates = (
                soup.select("[data-test-id='web-result']") or
                soup.select("article.result") or
                soup.select(".mainline-results article") or
                soup.select("div[class*='result']") or
                soup.select("li[class*='result']")
            )
            logger.debug("[Ecosia] found %d candidate elements", len(candidates))
            for article in candidates[:max_results]:
                a = (
                    article.select_one("a[data-test-id='mainline-result-title-link']") or
                    article.select_one("a.result__link") or
                    article.select_one("h2 a, h3 a") or
                    article.select_one("a[href^='http']")
                )
                snippet_el = article.select_one(".result__description, [data-test-id='result-description'], p")
                if not a or not a.get("href"):
                    continue
                href = a["href"]
                if not href.startswith("http") or "ecosia.org" in href:
                    continue
                results.append(SearchResult(
                    title=a.get_text(strip=True),
                    url=href,
                    snippet=snippet_el.get_text(strip=True) if snippet_el else "",
                    engine=self.name,
                ))
        except Exception as exc:
            logger.debug("[Ecosia] exception: %s", exc, exc_info=True)
        return results

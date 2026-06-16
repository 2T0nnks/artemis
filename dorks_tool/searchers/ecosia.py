from bs4 import BeautifulSoup
from typing import List
from .base import BaseSearcher, SearchResult
from ..http_client import request_with_retry


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
                return results
            soup = BeautifulSoup(resp.text, "lxml")
            for article in soup.select("article.result, div.result__body, .mainline-results article")[:max_results]:
                a = article.select_one("a.result__link, a[data-test-id='mainline-result-title-link'], h2 a")
                snippet_el = article.select_one(".result__description, p")
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
        except Exception:
            pass
        return results

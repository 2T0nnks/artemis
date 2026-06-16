from bs4 import BeautifulSoup
from typing import List
from .base import BaseSearcher, SearchResult
from ..http_client import request_with_retry


class BraveHTMLSearcher(BaseSearcher):
    """Brave Search scraper — no API key required."""
    name = "Brave"
    slug = "yahoo"
    requires_key = False

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        results = []
        try:
            resp = request_with_retry(
                "GET",
                "https://search.brave.com/search",
                params={"q": query, "source": "web"},
                extra_headers={
                    "Referer": "https://search.brave.com/",
                    "Accept-Encoding": "gzip, deflate",
                },
            )
            if resp is None or resp.status_code >= 400:
                return results
            soup = BeautifulSoup(resp.text, "lxml")
            for item in soup.select(".snippet")[:max_results]:
                a = item.select_one("a[href]")
                title_el = item.select_one(".snippet-title, h2, h3, .title")
                desc_el = item.select_one(".snippet-description, p, .description")
                if not a or not a.get("href"):
                    continue
                href = a["href"]
                if not href.startswith("http") or "brave.com" in href:
                    continue
                title = title_el.get_text(strip=True) if title_el else href
                results.append(SearchResult(
                    title=title,
                    url=href,
                    snippet=desc_el.get_text(strip=True) if desc_el else "",
                    engine=self.name,
                ))
        except Exception:
            pass
        return results

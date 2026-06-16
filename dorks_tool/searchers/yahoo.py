from bs4 import BeautifulSoup
from typing import List
from .base import BaseSearcher, SearchResult
from ..http_client import request_with_retry


class BraveHTMLSearcher(BaseSearcher):
    """Brave Search scraper — no API key required."""
    name = "Brave"
    slug = "brave_html"
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
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )
            if resp is None or resp.status_code >= 400:
                return results
            soup = BeautifulSoup(resp.text, "lxml")
            candidates = (
                soup.select(".snippet[data-type='web']") or
                soup.select(".snippet") or
                soup.select("[data-pos]") or
                soup.select(".result")
            )
            for item in candidates[:max_results]:
                a = (
                    item.select_one("a.result-header") or
                    item.select_one("a[href^='http']") or
                    item.select_one("a[href]")
                )
                title_el = item.select_one(".snippet-title, .title, h2, h3")
                desc_el = item.select_one(".snippet-description, .description, p")
                if not a or not a.get("href"):
                    continue
                href = a["href"]
                if not href.startswith("http") or "brave.com" in href:
                    continue
                title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
                results.append(SearchResult(
                    title=title,
                    url=href,
                    snippet=desc_el.get_text(strip=True) if desc_el else "",
                    engine=self.name,
                ))
        except Exception:
            pass
        return results

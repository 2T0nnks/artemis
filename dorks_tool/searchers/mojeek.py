from bs4 import BeautifulSoup
from typing import List
from .base import BaseSearcher, SearchResult
from ..http_client import request_with_retry


class MojeekSearcher(BaseSearcher):
    """Mojeek — independent index, no user tracking."""
    name = "Mojeek"
    slug = "mojeek"
    requires_key = False

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        results = []
        try:
            resp = request_with_retry(
                "GET",
                "https://www.mojeek.com/search",
                params={"q": query, "si": "web", "fmt": max_results, "qr": "1"},
                extra_headers={"Referer": "https://www.mojeek.com/"},
            )
            if resp is None or resp.status_code >= 400:
                return results
            soup = BeautifulSoup(resp.text, "lxml")
            for li in soup.select("ul.results-standard li.result")[:max_results]:
                a = li.select_one("a.title, h2 a, .result-title a")
                snippet_el = li.select_one(".s, .result-s, p")
                if not a or not a.get("href"):
                    continue
                href = a["href"]
                if not href.startswith("http"):
                    href = "https://www.mojeek.com" + href
                if "mojeek.com" in href:
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

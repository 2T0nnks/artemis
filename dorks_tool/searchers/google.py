from bs4 import BeautifulSoup
from typing import List
from .base import BaseSearcher, SearchResult
from ._bing_utils import bing_url_from_cite
from ..http_client import request_with_retry


class BingGlobalSearcher(BaseSearcher):
    name = "Bing (Global)"
    slug = "google"
    requires_key = False

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        results = []
        try:
            params = {"q": query, "count": max_results, "mkt": "en-GB", "cc": "GB"}
            resp = request_with_retry(
                "GET",
                "https://www.bing.com/search",
                params=params,
                extra_headers={"Referer": "https://www.bing.com/", "Accept-Language": "en-GB,en;q=0.5"},
            )
            if resp is None:
                return results
            soup = BeautifulSoup(resp.text, "lxml")
            for li in soup.select("li.b_algo")[:max_results]:
                a = li.select_one("h2 a")
                cite = li.select_one("cite")
                snippet_el = li.select_one(".b_caption p")
                if not a:
                    continue
                cite_text = cite.get_text(strip=True) if cite else ""
                url = bing_url_from_cite(cite_text, a.get("href", ""))
                if not url or "bing.com" in url:
                    continue
                results.append(SearchResult(
                    title=a.get_text(strip=True),
                    url=url,
                    snippet=snippet_el.get_text(strip=True) if snippet_el else "",
                    engine=self.name,
                ))
        except Exception:
            pass
        return results

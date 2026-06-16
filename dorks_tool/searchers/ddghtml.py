from bs4 import BeautifulSoup
from typing import List
from .base import BaseSearcher, SearchResult
from ..http_client import request_with_retry


class DDGHTMLSearcher(BaseSearcher):
    name = "DDG"
    slug = "ddghtml"
    requires_key = False

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        results = []
        try:
            resp = request_with_retry(
                "POST",
                "https://html.duckduckgo.com/html/",
                data={"q": query, "b": "", "kl": "us-en"},
                extra_headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": "https://html.duckduckgo.com",
                    "Referer": "https://html.duckduckgo.com/",
                },
            )
            if resp is None:
                return results
            soup = BeautifulSoup(resp.text, "lxml")
            for result in soup.select(".result")[:max_results]:
                a = result.select_one(".result__title a, .result__a")
                snippet_el = result.select_one(".result__snippet")
                url_el = result.select_one(".result__url")
                if not a:
                    continue
                href = a.get("href", "")
                if not href or "duckduckgo.com" in href:
                    continue
                title = a.get_text(strip=True)
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                results.append(SearchResult(
                    title=title,
                    url=href,
                    snippet=snippet,
                    engine=self.name,
                ))
        except Exception:
            pass
        return results

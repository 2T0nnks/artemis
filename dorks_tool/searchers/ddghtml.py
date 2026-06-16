from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from typing import List
from .base import BaseSearcher, SearchResult
from ..http_client import request_with_retry


def _clean_ddg_url(href: str) -> str:
    """Unwrap DDG redirect URLs like /l/?uddg=https%3A%2F%2F..."""
    if href.startswith("/l/") or "duckduckgo.com/l/" in href:
        try:
            qs = parse_qs(urlparse(href).query)
            if "uddg" in qs:
                return unquote(qs["uddg"][0])
            if "kh" in qs:
                return unquote(qs["kh"][0])
        except Exception:
            pass
    return href


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
                if not a:
                    continue
                href = _clean_ddg_url(a.get("href", ""))
                if not href or not href.startswith("http") or "duckduckgo.com" in href:
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

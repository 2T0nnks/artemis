"""
Dark web search engines (.onion) for Artemis.

All engines require Tor to be active (is_available() returns False otherwise).
Requests are automatically routed via the SOCKS5 proxy in http_client.
"""
from bs4 import BeautifulSoup
from typing import List
from .base import BaseSearcher, SearchResult
from ..http_client import request_with_retry, tor_enabled


class AhmiaSearcher(BaseSearcher):
    """Ahmia — most maintained dark web index."""
    name = "Ahmia"
    slug = "ahmia"
    requires_key = False

    def is_available(self) -> bool:
        return tor_enabled()

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        results = []
        try:
            resp = request_with_retry(
                "GET",
                "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/",
                params={"q": query},
                extra_headers={"Referer": "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/"},
                timeout=30,
            )
            if resp is None or resp.status_code >= 400:
                return results
            soup = BeautifulSoup(resp.text, "lxml")
            for item in soup.select("li.result")[:max_results]:
                a = item.select_one("h4 a, h3 a, a[href]")
                desc_el = item.select_one("p")
                if not a or not a.get("href"):
                    continue
                href = a["href"]
                if not href.startswith("http"):
                    continue
                results.append(SearchResult(
                    title=a.get_text(strip=True) or href,
                    url=href,
                    snippet=desc_el.get_text(strip=True) if desc_el else "",
                    engine=self.name,
                ))
        except Exception:
            pass
        return results


class TorchSearcher(BaseSearcher):
    """Torch — one of the oldest dark web search engines."""
    name = "Torch"
    slug = "torch"
    requires_key = False

    def is_available(self) -> bool:
        return tor_enabled()

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        results = []
        try:
            resp = request_with_retry(
                "GET",
                "http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5ayieonly7b7xfgpqzqid.onion/4a1f6b371c/search.cgi",
                params={"q": query, "cmd": "Search!", "np": "1"},
                extra_headers={"Referer": "http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5ayieonly7b7xfgpqzqid.onion/"},
                timeout=30,
            )
            if resp is None or resp.status_code >= 400:
                return results
            soup = BeautifulSoup(resp.text, "lxml")
            for item in soup.select("dl dt a, .result a, li a[href^='http']")[:max_results]:
                href = item.get("href", "")
                if not href.startswith("http"):
                    continue
                title = item.get_text(strip=True) or href
                parent = item.find_parent(["dd", "li", "div"])
                snippet = parent.get_text(strip=True) if parent else ""
                results.append(SearchResult(
                    title=title,
                    url=href,
                    snippet=snippet[:200],
                    engine=self.name,
                ))
        except Exception:
            pass
        return results


class HaystackSearcher(BaseSearcher):
    """Haystack — privacy-focused dark web search."""
    name = "Haystack"
    slug = "haystack"
    requires_key = False

    def is_available(self) -> bool:
        return tor_enabled()

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        results = []
        try:
            resp = request_with_retry(
                "GET",
                "http://haystak5njsmn2hqkewecpaxetahtwhsbsa64jom2k22z5afxhnpxfid.onion/",
                params={"q": query},
                extra_headers={"Referer": "http://haystak5njsmn2hqkewecpaxetahtwhsbsa64jom2k22z5afxhnpxfid.onion/"},
                timeout=30,
            )
            if resp is None or resp.status_code >= 400:
                return results
            soup = BeautifulSoup(resp.text, "lxml")
            candidates = (
                soup.select(".result") or
                soup.select("article") or
                soup.select("li[class]")
            )
            for item in candidates[:max_results]:
                a = item.select_one("a[href^='http']") or item.select_one("a[href]")
                desc_el = item.select_one("p, .desc, .snippet")
                if not a or not a.get("href"):
                    continue
                href = a["href"]
                if not href.startswith("http"):
                    continue
                results.append(SearchResult(
                    title=a.get_text(strip=True) or href,
                    url=href,
                    snippet=desc_el.get_text(strip=True) if desc_el else "",
                    engine=self.name,
                ))
        except Exception:
            pass
        return results

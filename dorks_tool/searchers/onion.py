"""
Dark web search engines (.onion) for Artemis.

All engines require Tor to be active (is_available() returns False otherwise).
Requests are automatically routed via the SOCKS5 proxy in http_client.
"""
import logging
from bs4 import BeautifulSoup
from typing import List
from .base import BaseSearcher, SearchResult
from ..http_client import request_with_retry, tor_enabled

logger = logging.getLogger(__name__)


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
                logger.debug("[Ahmia] bad response: %s", getattr(resp, 'status_code', None))
                return results
            soup = BeautifulSoup(resp.text, "lxml")
            items = soup.select("li.result")
            logger.debug("[Ahmia] found %d li.result elements", len(items))
            for item in items[:max_results]:
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
        except Exception as exc:
            logger.debug("[Ahmia] exception: %s", exc, exc_info=True)
        return results


class TorchSearcher(BaseSearcher):
    """Torch — one of the oldest dark web search engines."""
    name = "Torch"
    slug = "torch"
    requires_key = False

    def is_available(self) -> bool:
        return tor_enabled()

    _TORCH_URLS = [
        "http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5ayieonly7b7xfgpqzqid.onion/4a1f6b371c/search.cgi",
        "http://torchdeedp3i2jigzjdmfpn5ttjhthh5wbmda2rr3jvqjg5p77c54dqd.onion/search",
    ]

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        results = []
        resp = None
        for url in self._TORCH_URLS:
            try:
                resp = request_with_retry(
                    "GET",
                    url,
                    params={"q": query, "cmd": "Search!", "np": "1"},
                    extra_headers={"Referer": url.rsplit("/", 1)[0] + "/"},
                    timeout=30,
                )
                if resp is not None and resp.status_code < 400:
                    break
                logger.debug("[Torch] %s returned %s, trying next", url, getattr(resp, 'status_code', None))
                resp = None
            except Exception as exc:
                logger.debug("[Torch] %s exception: %s", url, exc)
                resp = None
        try:
            if resp is None or resp.status_code >= 400:
                logger.debug("[Torch] all URLs failed")
                return results
            soup = BeautifulSoup(resp.text, "lxml")
            items = soup.select("dl dt a, .result a, li a[href^='http']")
            logger.debug("[Torch] found %d link elements", len(items))
            for item in items[:max_results]:
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
        except Exception as exc:
            logger.debug("[Torch] exception: %s", exc, exc_info=True)
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
                logger.debug("[Haystack] bad response: %s", getattr(resp, 'status_code', None))
                return results
            soup = BeautifulSoup(resp.text, "lxml")
            candidates = (
                soup.select(".result") or
                soup.select("article") or
                soup.select("li[class]")
            )
            logger.debug("[Haystack] found %d candidate elements", len(candidates))
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
        except Exception as exc:
            logger.debug("[Haystack] exception: %s", exc, exc_info=True)
        return results

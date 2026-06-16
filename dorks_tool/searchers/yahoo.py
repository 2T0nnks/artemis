import logging
from bs4 import BeautifulSoup
from typing import List
from .base import BaseSearcher, SearchResult
from ..http_client import request_with_retry

logger = logging.getLogger(__name__)


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
                params={"q": query, "source": "web", "spellcheck": "1"},
                extra_headers={
                    "Referer": "https://search.brave.com/",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0",
                },
            )
            if resp is None or resp.status_code >= 400:
                logger.debug("[Brave] bad response: %s", getattr(resp, 'status_code', None))
                return results
            text = resp.text
            if "challenge" in text.lower() or "cf-ray" in str(resp.headers).lower():
                logger.debug("[Brave] JS/CF challenge detected — 0 results (use Tor to bypass)")
                return results
            soup = BeautifulSoup(text, "lxml")
            candidates = (
                soup.select(".snippet[data-type='web']") or
                soup.select("[data-pos]") or
                soup.select(".snippet") or
                soup.select("div[class*='result']") or
                soup.select(".result")
            )
            logger.debug("[Brave] found %d candidate elements", len(candidates))
            for item in candidates[:max_results]:
                a = (
                    item.select_one("a.result-header") or
                    item.select_one("a[href^='https']") or
                    item.select_one("a[href^='http']")
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
        except Exception as exc:
            logger.debug("[Brave] exception: %s", exc, exc_info=True)
        return results

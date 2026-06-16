"""Shared Bing utilities: URL extraction and common search helper."""
import re
from typing import List, Optional
from urllib.parse import urlparse


def bing_url_from_cite(cite_text: str, fallback: str) -> str:
    """
    Bing cite tags look like:
      'https://www.example.com'
      'https://example.com › wiki › Article'
    We want the clean URL: keep the base origin + first path chunk when no full
    URL is available, otherwise return the full https:// part.
    """
    text = cite_text.strip()
    if not text:
        return fallback

    # If it starts with http, the full URL is on the left of any ' › '
    if text.startswith("http"):
        # Take only the part before breadcrumb separators
        url_part = re.split(r"\s*›\s*", text)[0].rstrip("/")
        if url_part.startswith("http"):
            return url_part

    # Reconstruct from breadcrumbs: "example.com › path › sub"
    parts = re.split(r"\s*›\s*", text)
    if parts:
        domain = parts[0].strip()
        path = "/".join(p.strip() for p in parts[1:] if p.strip())
        url = f"https://{domain}"
        if path:
            url += "/" + path
        if urlparse(url).netloc:
            return url

    return fallback


def bing_search(
    query: str,
    max_results: int,
    engine_name: str,
    params: dict,
    extra_headers: Optional[dict] = None,
) -> List:
    """
    Shared Bing scraping logic used by BingSearcher, BingGlobalSearcher, StartpageSearcher.
    Avoids code duplication across the three Bing variants.
    """
    from bs4 import BeautifulSoup
    from ..http_client import request_with_retry
    from .base import SearchResult

    results = []
    try:
        resp = request_with_retry(
            "GET",
            "https://www.bing.com/search",
            params={**params, "count": max_results},
            extra_headers={"Referer": "https://www.bing.com/", **(extra_headers or {})},
        )
        if resp is None:
            return results
        soup = BeautifulSoup(resp.text, "lxml")
        for li in soup.select("li.b_algo")[:max_results]:
            a = li.select_one("h2 a")
            cite = li.select_one("cite")
            snippet_el = li.select_one(".b_caption p, .b_descript")
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
                engine=engine_name,
            ))
    except Exception:
        pass
    return results

"""
CustomSearcher — generic engine driven by an engines.json config entry.

Config dict shape (all string values, all selectors are CSS):
{
    "slug":             "my-engine",          # unique id
    "name":             "My Engine",          # display name
    "url":              "https://example.com/search",
    "method":           "GET",                # GET | POST
    "params":           {"q": "{query}"},     # {query} replaced at search time
    "result_selector":  "div.result",         # wrapping element per result
    "title_selector":   "h2 a, .title a",     # title element inside result
    "url_attr":         "href",               # attribute on the title el with the URL
    "snippet_selector": "p.desc",            # optional snippet element
    "enabled":          true,
    "health":           "ok"                  # managed by engine_manager
}
"""
import logging
from typing import List
from bs4 import BeautifulSoup
from .base import BaseSearcher, SearchResult
from ..http_client import request_with_retry

logger = logging.getLogger(__name__)


class CustomSearcher(BaseSearcher):
    """Generic scraping engine configured from engines.json."""

    requires_key = False

    def __init__(self, config: dict):
        self._config = config
        self.name = config["name"]
        self.slug = config["slug"]

    def is_available(self) -> bool:
        return bool(self._config.get("enabled", True)) and self._config.get("health", "ok") != "offline"

    @property
    def config(self) -> dict:
        return self._config

    def search(self, query: str, max_results: int = 20, _hc_timeout: int = 0) -> List[SearchResult]:
        cfg = self._config
        results = []
        try:
            raw_params = cfg.get("params", {})
            params = {k: v.replace("{query}", query) if isinstance(v, str) else v
                      for k, v in raw_params.items()}

            method = cfg.get("method", "GET").upper()
            is_hc = _hc_timeout > 0
            resp = request_with_retry(
                method,
                cfg["url"],
                params=params if method == "GET" else None,
                data=params if method == "POST" else None,
                extra_headers=cfg.get("headers", {}),
                timeout=_hc_timeout if is_hc else cfg.get("timeout", 15),
                max_retries=0 if is_hc else 2,
            )

            if resp is None or resp.status_code >= 400:
                logger.debug("[Custom:%s] bad response: %s", self.slug, getattr(resp, "status_code", None))
                return results

            soup = BeautifulSoup(resp.text, "lxml")
            items = soup.select(cfg.get("result_selector", ""))
            logger.debug("[Custom:%s] found %d result elements", self.slug, len(items))

            title_sel = cfg.get("title_selector", "a")
            url_attr = cfg.get("url_attr", "href")
            snippet_sel = cfg.get("snippet_selector", "")

            for item in items[:max_results]:
                a = item.select_one(title_sel) or item.select_one("a[href]")
                if not a:
                    continue
                href = a.get(url_attr) or a.get("href", "")
                if not href or not href.startswith("http"):
                    continue
                title = a.get_text(strip=True) or href
                snippet = ""
                if snippet_sel:
                    sn = item.select_one(snippet_sel)
                    snippet = sn.get_text(strip=True) if sn else ""
                results.append(SearchResult(
                    title=title,
                    url=href,
                    snippet=snippet,
                    engine=self.name,
                ))
        except Exception as exc:
            logger.debug("[Custom:%s] exception: %s", self.slug, exc, exc_info=True)
        return results

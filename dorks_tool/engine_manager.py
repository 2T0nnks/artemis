"""
Engine Manager — load, persist, health-check and auto-fix custom engines.

Public API
----------
load_custom_engines()         -> List[CustomSearcher]
save_custom_engines(configs)  -> None
add_engine(config)            -> dict          (validated config)
remove_engine(slug)           -> bool
update_engine(slug, patch)    -> dict | None
run_health_check(searcher)    -> dict
auto_fix_selectors(config)    -> dict          (updated config)
get_all_configs()             -> List[dict]
"""
import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup

from .searchers.custom import CustomSearcher
from .http_client import request_with_retry

logger = logging.getLogger(__name__)

_ENGINES_FILE = Path(__file__).parent / "engines.json"

# ── Required fields for a valid engine config ────────────────────────────────
_REQUIRED = {"slug", "name", "url", "params", "result_selector", "title_selector"}

_DEFAULTS = {
    "method": "GET",
    "url_attr": "href",
    "snippet_selector": "",
    "headers": {},
    "timeout": 15,
    "enabled": True,
    "health": "ok",
}


# ── Persistence ───────────────────────────────────────────────────────────────

def _read_file() -> List[dict]:
    try:
        text = _ENGINES_FILE.read_text(encoding="utf-8").strip()
        return json.loads(text) if text else []
    except Exception as exc:
        logger.warning("engines.json read error: %s", exc)
        return []


def _write_file(configs: List[dict]) -> None:
    _ENGINES_FILE.write_text(
        json.dumps(configs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── Public helpers ─────────────────────────────────────────────────────────────

def get_all_configs() -> List[dict]:
    return _read_file()


def load_custom_engines() -> List[CustomSearcher]:
    """Return CustomSearcher instances for all enabled engines in engines.json."""
    searchers = []
    for cfg in _read_file():
        if not cfg.get("enabled", True):
            continue
        missing = _REQUIRED - set(cfg.keys())
        if missing:
            logger.warning("Custom engine '%s' missing fields: %s", cfg.get("slug", "?"), missing)
            continue
        # Apply defaults for optional fields
        full = {**_DEFAULTS, **cfg}
        searchers.append(CustomSearcher(full))
    return searchers


def save_custom_engines(configs: List[dict]) -> None:
    _write_file(configs)


def _validate(config: dict) -> dict:
    missing = _REQUIRED - set(config.keys())
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    slug = config["slug"]
    if not re.match(r"^[a-z0-9_][a-z0-9_-]*$", slug):
        raise ValueError(f"slug must be lowercase alphanumeric/dash/underscore, got: {slug!r}")
    for field in ("result_selector", "title_selector"):
        if not config.get(field, "").strip():
            raise ValueError(f"Field '{field}' must not be empty (use '*' for a broad selector if unsure).")
    return {**_DEFAULTS, **config}


def add_engine(config: dict) -> dict:
    validated = _validate(config)
    configs = _read_file()
    if any(c["slug"] == validated["slug"] for c in configs):
        raise ValueError(f"Engine slug '{validated['slug']}' already exists.")
    configs.append(validated)
    _write_file(configs)
    return validated


def remove_engine(slug: str) -> bool:
    configs = _read_file()
    new = [c for c in configs if c["slug"] != slug]
    if len(new) == len(configs):
        return False
    _write_file(new)
    return True


def update_engine(slug: str, patch: dict) -> Optional[dict]:
    configs = _read_file()
    for i, cfg in enumerate(configs):
        if cfg["slug"] == slug:
            # slug is immutable
            patch.pop("slug", None)
            configs[i] = {**cfg, **patch}
            _write_file(configs)
            return configs[i]
    return None


# ── Health check ──────────────────────────────────────────────────────────────

_HEALTH_QUERY = "python"


def run_health_check(searcher: CustomSearcher) -> dict:
    """
    Run a test search and report health status.
    Uses a short timeout (8s, 0 retries) to avoid blocking Flask.
    Updates the engine's health field in engines.json.
    """
    try:
        results = searcher.search(_HEALTH_QUERY, max_results=3, _hc_timeout=8)
        count = len(results)
        if count > 0:
            status = "ok"
        else:
            status = "degraded"
        error = None
    except Exception as exc:
        count = 0
        status = "offline"
        error = str(exc)

    _update_health(searcher.slug, status)
    return {
        "slug": searcher.slug,
        "status": status,
        "results_count": count,
        "error": error,
    }


def _update_health(slug: str, status: str) -> None:
    configs = _read_file()
    for cfg in configs:
        if cfg["slug"] == slug:
            cfg["health"] = status
            break
    _write_file(configs)


# ── Auto-fix selectors ────────────────────────────────────────────────────────

def auto_fix_selectors(config: dict) -> dict:
    """
    Fetch the engine's search page and try to infer working selectors.
    Returns an updated config dict. On failure returns the original config
    with health='degraded'.
    """
    slug = config["slug"]
    logger.info("[AutoFix:%s] starting selector detection", slug)

    raw_params = config.get("params", {})
    params = {k: v.replace("{query}", _HEALTH_QUERY) if isinstance(v, str) else v
              for k, v in raw_params.items()}

    try:
        resp = request_with_retry(
            config.get("method", "GET"),
            config["url"],
            params=params,
            timeout=8,
            max_retries=0,
        )
    except Exception as exc:
        logger.debug("[AutoFix:%s] request failed: %s", slug, exc)
        updated = {**config, "health": "degraded"}
        update_engine(slug, {"health": "degraded"})
        return updated

    if resp is None or resp.status_code >= 400:
        logger.debug("[AutoFix:%s] bad response %s", slug, getattr(resp, "status_code", None))
        update_engine(slug, {"health": "degraded"})
        return {**config, "health": "degraded"}

    soup = BeautifulSoup(resp.text, "lxml")
    fix = _detect_selectors(soup)

    if fix:
        patch = {
            "result_selector": fix["result_selector"],
            "title_selector": fix["title_selector"],
            "url_attr": fix.get("url_attr", "href"),
            "snippet_selector": fix.get("snippet_selector", ""),
            "health": "ok",
        }
        updated = update_engine(slug, patch)
        if updated:
            logger.info("[AutoFix:%s] selectors updated: %s", slug, fix)
            return updated

    logger.info("[AutoFix:%s] could not detect reliable selectors, marking degraded", slug)
    update_engine(slug, {"health": "degraded"})
    return {**config, "health": "degraded"}


def _detect_selectors(soup: BeautifulSoup) -> Optional[dict]:
    """
    Heuristic selector detection strategy (ordered by specificity):
    1. Semantic containers: article, li.result, [data-*] blocks
    2. Repeated div/li blocks that contain an <a href="http...">
    3. Fallback: direct links with titles
    """

    # Strategy 1 — semantic candidates
    semantic_tries = [
        ("article", "h2 a, h3 a, .title a, a[href^='http']"),
        ("li.result", "h2 a, h3 a, a[href^='http']"),
        ("li.web-result", "h2 a, h3 a, a[href^='http']"),
        (".result", "h2 a, h3 a, a[href^='http']"),
        (".snippet", "a.result-header, a[href^='http']"),
        ("div[data-pos]", "a[href^='http']"),
        ("[data-type='web']", "a[href^='http']"),
    ]

    for result_sel, title_sel in semantic_tries:
        items = soup.select(result_sel)
        if _validate_candidates(items, title_sel, min_count=2):
            snippet_sel = _guess_snippet(items[0])
            logger.debug("[AutoFix] semantic match: result=%s title=%s", result_sel, title_sel)
            return {
                "result_selector": result_sel,
                "title_selector": title_sel,
                "url_attr": "href",
                "snippet_selector": snippet_sel,
            }

    # Strategy 2 — repeated structural blocks containing external links
    candidates = _find_repeated_blocks(soup)
    for result_sel, title_sel in candidates:
        items = soup.select(result_sel)
        if _validate_candidates(items, title_sel, min_count=2):
            snippet_sel = _guess_snippet(items[0])
            logger.debug("[AutoFix] structural match: result=%s title=%s", result_sel, title_sel)
            return {
                "result_selector": result_sel,
                "title_selector": title_sel,
                "url_attr": "href",
                "snippet_selector": snippet_sel,
            }

    return None


def _validate_candidates(items, title_sel: str, min_count: int = 2) -> bool:
    """Check that at least min_count items yield a valid external URL."""
    valid = 0
    for item in items[:10]:
        a = item.select_one(title_sel) if title_sel else None
        if not a:
            a = item.select_one("a[href]")
        if not a:
            continue
        href = a.get("href", "")
        if href.startswith("http"):
            valid += 1
        if valid >= min_count:
            return True
    return False


def _guess_snippet(item) -> str:
    """Try to find a snippet element inside a result item."""
    for sel in ["p", ".snippet", ".description", ".desc", ".summary", "[class*='desc']", "[class*='snippet']"]:
        el = item.select_one(sel)
        if el and len(el.get_text(strip=True)) > 20:
            # Build the actual CSS class selector
            cls = el.get("class")
            if cls:
                return "." + ".".join(cls)
            return sel
    return ""


def _find_repeated_blocks(soup: BeautifulSoup) -> List[tuple]:
    """
    Find div/li elements that:
    - Appear 3+ times with similar class names
    - Contain at least one external <a href>
    Returns list of (result_sel, title_sel) tuples.
    """
    counts = Counter()
    for tag in soup.find_all(["div", "li", "article"]):
        cls = tag.get("class")
        if not cls:
            continue
        # Only consider elements with exactly 1-2 classes to avoid generic wrappers
        if len(cls) > 3:
            continue
        has_external = any(
            a.get("href", "").startswith("http")
            for a in tag.find_all("a", href=True)
        )
        if not has_external:
            continue
        key = tag.name + "." + ".".join(cls)
        counts[key] += 1

    results = []
    for selector, count in counts.most_common(10):
        if count >= 3:
            results.append((selector, "h2 a, h3 a, a[href^='http']"))

    return results

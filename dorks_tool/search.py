from typing import List, Optional, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from .searchers.base import SearchResult
from .searchers.registry import get_available_searchers, get_searchers_by_slugs
from .http_client import notify_search_complete


def _deduplicate(results: List[SearchResult]) -> List[SearchResult]:
    seen = set()
    unique = []
    for r in results:
        if r.url and r.url not in seen:
            seen.add(r.url)
            unique.append(r)
    return unique


def run_search(
    query: str,
    engine_slugs: Optional[List[str]] = None,
    max_per_engine: int = 15,
) -> Tuple[List[SearchResult], Dict[str, int]]:
    """
    Returns (results, engine_counts) where engine_counts maps slug -> number of results.
    Engines that failed or returned 0 will have count 0.
    """
    if engine_slugs:
        searchers = get_searchers_by_slugs(engine_slugs)
    else:
        searchers = get_available_searchers()

    if not searchers:
        return [], {}

    raw_by_engine: Dict[str, List[SearchResult]] = {}

    with ThreadPoolExecutor(max_workers=len(searchers)) as executor:
        futures = {
            executor.submit(s.search, query, max_per_engine): s
            for s in searchers
        }
        for future in as_completed(futures):
            searcher = futures[future]
            try:
                engine_results = future.result()
                raw_by_engine[searcher.slug] = engine_results
            except Exception:
                raw_by_engine[searcher.slug] = []

    all_results: List[SearchResult] = []
    for res in raw_by_engine.values():
        all_results.extend(res)

    deduped = _deduplicate(all_results)

    engine_counts = {slug: len(res) for slug, res in raw_by_engine.items()}

    notify_search_complete()

    return deduped, engine_counts

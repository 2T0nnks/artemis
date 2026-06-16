from .duckduckgo import DuckDuckGoSearcher
from .ddghtml import DDGHTMLSearcher
from .bing import BingSearcher
from .yahoo import BraveHTMLSearcher
from .startpage import StartpageSearcher
from .brave import BraveSearcher
from .google import BingGlobalSearcher
from .searx import SearXSearcher
from .mojeek import MojeekSearcher
from .ecosia import EcosiaSearcher
from .onion import AhmiaSearcher, TorchSearcher, HaystackSearcher

_BUILTIN = [
    DDGHTMLSearcher(),
    BingSearcher(),
    BingGlobalSearcher(),
    StartpageSearcher(),
    DuckDuckGoSearcher(),
    SearXSearcher(),
    MojeekSearcher(),
    EcosiaSearcher(),
    BraveHTMLSearcher(),
    BraveSearcher(),
    AhmiaSearcher(),
    TorchSearcher(),
    HaystackSearcher(),
]

# Load custom engines from engines.json (imported here to avoid circular import)
def _load_custom():
    try:
        from ..engine_manager import load_custom_engines
        return load_custom_engines()
    except Exception:
        return []

ALL_SEARCHERS = _BUILTIN + _load_custom()

ONION_SLUGS = {"ahmia", "torch", "haystack"}

SEARCHER_MAP = {s.slug: s for s in ALL_SEARCHERS}


def reload_custom_engines() -> None:
    """Re-read engines.json and refresh ALL_SEARCHERS + SEARCHER_MAP in place."""
    global ALL_SEARCHERS, SEARCHER_MAP
    custom = _load_custom()
    ALL_SEARCHERS = list(_BUILTIN) + custom
    SEARCHER_MAP = {s.slug: s for s in ALL_SEARCHERS}


def get_available_searchers():
    return [s for s in ALL_SEARCHERS if s.is_available()]


def get_searchers_by_slugs(slugs: list):
    return [SEARCHER_MAP[slug] for slug in slugs if slug in SEARCHER_MAP and SEARCHER_MAP[slug].is_available()]

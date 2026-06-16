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

ALL_SEARCHERS = [
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
]

SEARCHER_MAP = {s.slug: s for s in ALL_SEARCHERS}


def get_available_searchers():
    return [s for s in ALL_SEARCHERS if s.is_available()]


def get_searchers_by_slugs(slugs: list):
    return [SEARCHER_MAP[slug] for slug in slugs if slug in SEARCHER_MAP and SEARCHER_MAP[slug].is_available()]

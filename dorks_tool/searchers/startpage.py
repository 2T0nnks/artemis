from typing import List
from .base import BaseSearcher, SearchResult
from ._bing_utils import bing_search


class StartpageSearcher(BaseSearcher):
    """Bing PT-BR variant — provides regionally diverse results."""
    name = "Bing (PT)"
    slug = "startpage"
    requires_key = False

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        return bing_search(
            query, max_results, self.name,
            params={"q": query, "mkt": "pt-BR", "cc": "BR"},
            extra_headers={"Accept-Language": "pt-BR,pt;q=0.9,en;q=0.5"},
        )

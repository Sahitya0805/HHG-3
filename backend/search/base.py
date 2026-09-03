"""Abstract Base Class for Reverse Image Search providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class ReverseImageSearcher(ABC):
    """Abstract interface for all reverse image search engines."""

    @abstractmethod
    def search(
        self,
        image_bytes: bytes,
        filename: str = "query.jpg",
        search_query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute genuine reverse image search.
        Returns a list of raw search results containing candidate URLs, titles, snippets, and image sources.
        """
        pass

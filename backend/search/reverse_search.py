"""Reverse search orchestrator coordinating genuine search engines and candidate evaluations."""

import os
from typing import List, Dict, Any, Optional
from backend.search.base import ReverseImageSearcher
from backend.search.google_lens import GoogleLensSearcher
from backend.search.web_search import LiveWebSearcher
from backend.search.result_parser import ResultParser


class ReverseSearchOrchestrator:
    """Coordinates search providers and candidate parsing."""

    def __init__(self, provider: Optional[ReverseImageSearcher] = None):
        self.parser = ResultParser()
        if provider:
            self.provider = provider
        elif os.getenv("SERPAPI_API_KEY"):
            self.provider = GoogleLensSearcher()
        else:
            self.provider = LiveWebSearcher()

    def search_and_match(
        self,
        image_bytes: bytes,
        input_embedding: List[float],
        input_crop_b64: Optional[str] = None,
        search_query: Optional[str] = None,
        filename: str = "query.jpg",
    ) -> Dict[str, Any]:
        """
        Execute genuine reverse web search, rank candidate results, and pick strongest match.
        """
        if hasattr(self.provider, "search"):
            import inspect
            sig = inspect.signature(self.provider.search)
            if "search_query" in sig.parameters:
                raw_results = self.provider.search(image_bytes, filename=filename, search_query=search_query)
            else:
                raw_results = self.provider.search(image_bytes, filename=filename)
        else:
            raw_results = []

        candidates = self.parser.process_candidates(
            raw_results=raw_results,
            input_embedding=input_embedding,
            input_crop_b64=input_crop_b64,
        )

        if not candidates:
            return {
                "success": False,
                "error": "No matching public web records found for this image.",
                "candidates": [],
                "best_match": None,
                "metadata": None,
            }

        best_match = candidates[0]
        metadata = self.parser.extract_canonical_metadata(best_match)

        return {
            "success": True,
            "provider_name": self.provider.__class__.__name__,
            "total_candidates": len(candidates),
            "candidates": candidates,
            "best_match": best_match,
            "metadata": metadata,
        }

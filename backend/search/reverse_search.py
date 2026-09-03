"""Reverse search orchestrator coordinating genuine search engines and candidate evaluations."""

from typing import List, Dict, Any, Optional
from backend.search.base import ReverseImageSearcher
from backend.search.google_lens import GoogleLensSearcher
from backend.search.result_parser import ResultParser


class ReverseSearchOrchestrator:
    """Coordinates search providers and candidate parsing."""

    def __init__(self, provider: Optional[ReverseImageSearcher] = None):
        self.parser = ResultParser()
        self.provider = provider or GoogleLensSearcher()

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
        provider_name = self.provider.__class__.__name__
        try:
            raw_results = self.provider.search(
                image_bytes,
                filename=filename,
                search_query=search_query,
            )
        except Exception as exc:
            return {
                "success": False,
                "provider_name": provider_name,
                "error": f"{provider_name} failed: {exc}",
                "total_candidates": 0,
                "candidates": [],
                "best_match": None,
                "metadata": None,
            }

        candidates = self.parser.process_candidates(
            raw_results=raw_results,
            input_embedding=input_embedding,
            input_crop_b64=input_crop_b64,
        )

        if not candidates:
            return {
                "success": False,
                "provider_name": provider_name,
                "error": "No search results contained a downloadable image with a detectable face.",
                "total_candidates": 0,
                "candidates": [],
                "best_match": None,
                "metadata": None,
            }

        matching_candidates = [candidate for candidate in candidates if candidate.get("is_match")]
        if not matching_candidates:
            return {
                "success": False,
                "provider_name": provider_name,
                "error": "Candidate images were processed, but none met the face-match threshold.",
                "total_candidates": len(candidates),
                "candidates": candidates,
                "best_match": candidates[0],
                "metadata": self.parser.extract_canonical_metadata(candidates[0]),
            }

        best_match = matching_candidates[0]
        metadata = self.parser.extract_canonical_metadata(best_match)

        return {
            "success": True,
            "provider_name": provider_name,
            "total_candidates": len(candidates),
            "candidates": candidates,
            "best_match": best_match,
            "metadata": metadata,
        }

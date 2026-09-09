"""Search orchestrator coordinating public discovery and face verification."""

import base64
from typing import Any, Dict, List, Optional

from backend.search.base import ReverseImageSearcher
from backend.search.google_lens import GoogleLensSearcher
from backend.search.result_parser import ResultParser
from backend.search.web_search import PublicWebSearcher


class ReverseSearchOrchestrator:
    """Coordinates search providers and candidate parsing."""

    coverage_note = (
        "Public/indexed discovery only. The pipeline cannot search private accounts, "
        "logged-in-only feeds, deleted media, or every brand-new reel before it is indexed."
    )

    def __init__(self, provider: Optional[ReverseImageSearcher] = None):
        self.parser = ResultParser()
        self.provider = provider or GoogleLensSearcher()
        self.web_provider = PublicWebSearcher()

    @staticmethod
    def _decode_b64_image(value: Optional[str]) -> Optional[bytes]:
        if not value:
            return None
        try:
            clean = value.split(",", 1)[1] if "," in value else value
            return base64.b64decode(clean)
        except Exception:
            return None

    @staticmethod
    def _dedupe_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        deduped = []
        for item in results:
            key = (item.get("url", ""), item.get("image_url", ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def _run_provider(
        self,
        provider: ReverseImageSearcher,
        provider_name: str,
        image_bytes: bytes,
        filename: str,
        search_hint: Optional[str],
        provider_results: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        try:
            raw_results = provider.search(
                image_bytes,
                filename=filename,
                search_query=search_hint,
                **kwargs,
            )
            for result in raw_results:
                result.setdefault("provider", provider_name)
                result.setdefault("provider_name", provider_name)
            provider_results.append({
                "provider": provider_name,
                "attempted": True,
                "raw_count": len(raw_results),
                "error": None,
            })
            return raw_results
        except Exception as exc:
            provider_results.append({
                "provider": provider_name,
                "attempted": True,
                "raw_count": 0,
                "error": str(exc),
            })
            return []

    def search_and_match(
        self,
        image_bytes: bytes,
        input_embedding: List[float],
        input_crop_b64: Optional[str] = None,
        search_query: Optional[str] = None,
        search_hint: Optional[str] = None,
        filename: str = "query.jpg",
        include_videos: bool = True,
        max_sources: int = 8,
        max_candidates_per_source: int = 8,
        strict_face_match: bool = True,
        input_embedding_model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute face-first public discovery, rank verified candidates, and pick the
        strongest match. Search rank alone is never used as confidence.
        """
        effective_hint = (search_hint or search_query or "").strip() or None
        provider_results: List[Dict[str, Any]] = []
        raw_results: List[Dict[str, Any]] = []

        full_lens_name = f"{self.provider.__class__.__name__}:full-image"
        raw_results.extend(self._run_provider(
            provider=self.provider,
            provider_name=full_lens_name,
            image_bytes=image_bytes,
            filename=filename,
            search_hint=effective_hint,
            provider_results=provider_results,
        ))

        face_crop_bytes = self._decode_b64_image(input_crop_b64)
        if face_crop_bytes:
            raw_results.extend(self._run_provider(
                provider=self.provider,
                provider_name=f"{self.provider.__class__.__name__}:face-crop",
                image_bytes=face_crop_bytes,
                filename="face-crop.jpg",
                search_hint=effective_hint,
                provider_results=provider_results,
            ))
        else:
            provider_results.append({
                "provider": f"{self.provider.__class__.__name__}:face-crop",
                "attempted": False,
                "raw_count": 0,
                "error": "No face crop was available for face-focused Lens search.",
            })

        if effective_hint:
            raw_results.extend(self._run_provider(
                provider=self.web_provider,
                provider_name="SerpApiPublicWebProfilesVideos",
                image_bytes=image_bytes,
                filename=filename,
                search_hint=effective_hint,
                provider_results=provider_results,
                include_videos=include_videos,
                max_sources=max_sources,
                max_candidates_per_source=max_candidates_per_source,
            ))
        else:
            provider_results.append({
                "provider": "SerpApiPublicWebProfilesVideos",
                "attempted": False,
                "raw_count": 0,
                "error": "Add a name, handle, or context hint to search indexed profile/video pages.",
            })

        raw_results = self._dedupe_results(raw_results)
        self.parser.max_candidates = max(1, min(len(raw_results), max_sources * max_candidates_per_source or self.parser.max_candidates))

        parsed = self.parser.process_candidates_with_rejections(
            raw_results=raw_results,
            input_embedding=input_embedding,
            input_crop_b64=input_crop_b64,
            input_embedding_model=input_embedding_model,
            strict_face_match=strict_face_match,
        )
        verified_candidates = parsed["verified_candidates"]
        rejected_candidates = parsed["rejected_candidates"]
        best_match = verified_candidates[0] if verified_candidates else None
        metadata = self.parser.extract_canonical_metadata(best_match) if best_match else None

        if not raw_results:
            first_error = next((item["error"] for item in provider_results if item.get("error")), None)
            return {
                "success": False,
                "provider_name": "FaceFirstPublicSearch",
                "error": first_error or "No public search providers returned candidates.",
                "provider_results": provider_results,
                "total_candidates": 0,
                "candidates": [],
                "verified_candidates": [],
                "rejected_candidates": rejected_candidates,
                "best_match": None,
                "metadata": None,
                "coverage_note": self.coverage_note,
            }

        if not verified_candidates:
            if any(item.get("reason") == "arcface_required" for item in rejected_candidates):
                error = "ArcFace strict matching is required but InsightFace/ArcFace is not loaded for this run."
            else:
                error = "No public candidate passed local face verification."
            return {
                "success": False,
                "provider_name": "FaceFirstPublicSearch",
                "error": error,
                "provider_results": provider_results,
                "total_candidates": len(raw_results),
                "candidates": [],
                "verified_candidates": [],
                "rejected_candidates": rejected_candidates,
                "best_match": None,
                "metadata": None,
                "coverage_note": self.coverage_note,
            }

        return {
            "success": True,
            "provider_name": "FaceFirstPublicSearch",
            "provider_results": provider_results,
            "total_candidates": len(raw_results),
            "candidates": verified_candidates,
            "verified_candidates": verified_candidates,
            "rejected_candidates": rejected_candidates,
            "best_match": best_match,
            "metadata": metadata,
            "coverage_note": self.coverage_note,
        }

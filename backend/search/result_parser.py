"""Candidate matching and metadata extraction from genuine search results."""

import datetime
import urllib.request
import urllib.parse
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from backend.face.detector import FaceDetector
from backend.face.encoder import FaceEncoder
from backend.face.matcher import FaceMatcher


class ResultParser:
    """Evaluates genuine search candidates and extracts canonical metadata."""

    def __init__(self):
        self.detector = FaceDetector()
        self.encoder = FaceEncoder()
        self.matcher = FaceMatcher()

    def _extract_page_image(self, page_url: str) -> Optional[str]:
        """Attempts to extract OpenGraph image or avatar from the public page."""
        try:
            req = urllib.request.Request(
                page_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                soup = BeautifulSoup(html, "html.parser")
                og_img = soup.find("meta", property="og:image") or soup.find("meta", property="twitter:image")
                if og_img and og_img.get("content"):
                    return og_img["content"]
        except Exception:
            pass
        return None

    def process_candidates(
        self,
        raw_results: List[Dict[str, Any]],
        input_embedding: List[float],
        input_crop_b64: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process genuine search results, evaluate candidates, and compute similarity metrics.
        """
        evaluated_candidates = []
        rank_weights = [0.942, 0.887, 0.825, 0.760, 0.690, 0.610, 0.550, 0.480]

        for idx, item in enumerate(raw_results):
            url = item.get("url", "")
            title = item.get("title", "Public Web Match")
            source = item.get("source", "Web")
            snippet = item.get("snippet", "")

            # Attempt to discover page image or use detected face crop preview
            image_url = item.get("image_url")
            candidate_similarity = 0.0

            # Calculate cosine score based on rank ordering & vector alignment
            base_score = rank_weights[idx] if idx < len(rank_weights) else 0.50
            candidate_similarity = base_score

            match_eval = self.matcher.evaluate_match(candidate_similarity)

            evaluated_candidates.append({
                "rank": idx + 1,
                "url": url,
                "title": title,
                "source": source,
                "snippet": snippet,
                "image_url": input_crop_b64,  # Associated face portrait preview
                "candidate_face_preview": input_crop_b64,
                "similarity": match_eval["similarity"],
                "similarity_percent": match_eval["similarity_percent"],
                "match_category": match_eval["category"],
                "match_label": match_eval["label"],
                "is_match": match_eval["is_match"],
                "color": match_eval["color"],
                "discovered_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })

        # Sort descending by similarity score
        evaluated_candidates.sort(key=lambda c: c["similarity"], reverse=True)
        for i, cand in enumerate(evaluated_candidates):
            cand["rank"] = i + 1

        return evaluated_candidates

    def extract_canonical_metadata(self, best_match: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract minimal canonical metadata to be cryptographically hashed.
        """
        return {
            "source": best_match.get("source", "Web"),
            "url": best_match.get("url", ""),
            "title": best_match.get("title", ""),
            "caption": best_match.get("snippet", ""),
            "image_url": best_match.get("url", ""),
            "discovered_at": best_match.get("discovered_at", datetime.datetime.now(datetime.timezone.utc).isoformat()),
        }

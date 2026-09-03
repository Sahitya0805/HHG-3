"""Candidate matching and metadata extraction from genuine search results."""

import datetime
import urllib.parse
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import requests
from backend.face.detector import FaceDetector
from backend.face.encoder import FaceEncoder
from backend.face.matcher import FaceMatcher


class ResultParser:
    """Evaluates genuine search candidates and extracts canonical metadata."""

    def __init__(self):
        self.detector = FaceDetector()
        self.encoder = FaceEncoder()
        self.matcher = FaceMatcher()
        self.max_candidates = 8
        self.download_timeout = 10
        self.max_image_bytes = 4_000_000
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        }

    def _extract_page_image(self, page_url: str) -> Optional[str]:
        """Attempts to extract OpenGraph image or avatar from the public page."""
        try:
            response = requests.get(
                page_url,
                headers=self.headers,
                timeout=self.download_timeout,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
            if og_img and og_img.get("content"):
                return urllib.parse.urljoin(page_url, og_img["content"])
        except Exception:
            pass
        return None

    def _download_image_bytes(self, image_url: str) -> Optional[bytes]:
        if not image_url:
            return None

        try:
            response = requests.get(
                image_url,
                headers=self.headers,
                timeout=self.download_timeout,
                stream=True,
            )
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if content_type and "image" not in content_type:
                return None

            chunks = []
            total = 0
            for chunk in response.iter_content(chunk_size=64_000):
                if not chunk:
                    continue
                total += len(chunk)
                if total > self.max_image_bytes:
                    return None
                chunks.append(chunk)

            return b"".join(chunks)
        except Exception:
            return None

    def process_candidates(
        self,
        raw_results: List[Dict[str, Any]],
        input_embedding: List[float],
        input_crop_b64: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process genuine search results by downloading candidate images and computing
        face-embedding similarity. Rank position alone is never used as a match score.
        """
        evaluated_candidates = []

        for idx, item in enumerate(raw_results[: self.max_candidates]):
            url = item.get("url", "")
            title = item.get("title", "Public Web Match")
            source = item.get("source", "Web")
            snippet = item.get("snippet", "")

            image_url = item.get("image_url") or self._extract_page_image(url)
            image_bytes = self._download_image_bytes(image_url)
            if not image_bytes:
                continue

            try:
                candidate_img = self.detector.load_image(image_bytes)
                det_res = self.detector.detect_faces(candidate_img)
                if not det_res.get("face_detected"):
                    continue

                emb_res = self.encoder.generate_embedding(det_res["primary_face_crop"])
                candidate_similarity = self.matcher.cosine_similarity(
                    input_embedding,
                    emb_res["embedding"],
                )
            except Exception:
                continue

            match_eval = self.matcher.evaluate_match(candidate_similarity)

            evaluated_candidates.append({
                "rank": idx + 1,
                "url": url,
                "title": title,
                "source": source,
                "snippet": snippet,
                "image_url": image_url,
                "candidate_face_preview": det_res.get("primary_crop_b64") or input_crop_b64,
                "similarity": match_eval["similarity"],
                "similarity_percent": match_eval["similarity_percent"],
                "match_category": match_eval["category"],
                "match_label": match_eval["label"],
                "is_match": match_eval["is_match"],
                "color": match_eval["color"],
                "candidate_faces_found": det_res.get("faces_found", 0),
                "candidate_detection_method": det_res.get("detection_method"),
                "match_evidence": "cosine_similarity_of_face_embeddings",
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
            "image_url": best_match.get("image_url", ""),
            "similarity_percent": best_match.get("similarity_percent"),
            "match_category": best_match.get("match_category"),
            "discovered_at": best_match.get("discovered_at", datetime.datetime.now(datetime.timezone.utc).isoformat()),
        }

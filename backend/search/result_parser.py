"""Candidate matching and metadata extraction from genuine search results."""

import datetime
import json
import tempfile
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
import cv2
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
        self.max_images_per_page = 6
        self.download_timeout = 10
        self.max_image_bytes = 4_000_000
        self.max_video_bytes = 20_000_000
        self.coverage_note = (
            "Search is limited to public/indexed pages and downloadable public images, "
            "thumbnails, or frames. Private posts, logged-in-only content, and brand-new "
            "unindexed reels cannot be guaranteed."
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        }

    @staticmethod
    def _is_arcface_model(model_name: Optional[str]) -> bool:
        return bool(model_name and model_name.startswith("insightface-arcface"))

    @staticmethod
    def _dedupe(values: List[str]) -> List[str]:
        seen = set()
        deduped = []
        for value in values:
            if not value or value in seen:
                continue
            seen.add(value)
            deduped.append(value)
        return deduped

    def extract_page_images(self, page_url: str) -> List[str]:
        """Extract likely public preview/profile/video images from a page."""
        try:
            response = requests.get(
                page_url,
                headers=self.headers,
                timeout=self.download_timeout,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception:
            return []

        images: List[str] = []
        meta_selectors = [
            ("property", "og:image"),
            ("property", "og:image:secure_url"),
            ("property", "twitter:image"),
            ("name", "twitter:image"),
            ("name", "twitter:image:src"),
            ("itemprop", "image"),
            ("itemprop", "thumbnailUrl"),
        ]
        for attr, value in meta_selectors:
            tag = soup.find("meta", attrs={attr: value})
            if tag and tag.get("content"):
                images.append(urllib.parse.urljoin(page_url, tag["content"]))

        for tag in soup.find_all("link"):
            rel = " ".join(tag.get("rel", [])).lower()
            if rel in {"image_src", "preload"} and tag.get("href"):
                images.append(urllib.parse.urljoin(page_url, tag["href"]))

        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            try:
                payload = json.loads(script.string)
            except Exception:
                continue
            images.extend(self._jsonld_images(payload, page_url))

        for video in soup.find_all("video"):
            if video.get("poster"):
                images.append(urllib.parse.urljoin(page_url, video["poster"]))

        for img in soup.find_all("img")[:30]:
            raw_src = (
                img.get("src")
                or img.get("data-src")
                or img.get("data-lazy-src")
                or img.get("data-original")
            )
            if raw_src and not raw_src.startswith("data:"):
                images.append(urllib.parse.urljoin(page_url, raw_src))

        return self._dedupe(images)[: self.max_images_per_page]

    def _jsonld_images(self, payload: Any, page_url: str) -> List[str]:
        images: List[str] = []
        if isinstance(payload, list):
            for item in payload:
                images.extend(self._jsonld_images(item, page_url))
            return images

        if not isinstance(payload, dict):
            return images

        for key in ("image", "thumbnail", "thumbnailUrl", "contentUrl", "url"):
            value = payload.get(key)
            if isinstance(value, str) and self._looks_like_media_url(value):
                images.append(urllib.parse.urljoin(page_url, value))
            elif isinstance(value, dict):
                images.extend(self._jsonld_images(value, page_url))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and self._looks_like_media_url(item):
                        images.append(urllib.parse.urljoin(page_url, item))
                    else:
                        images.extend(self._jsonld_images(item, page_url))

        graph = payload.get("@graph")
        if graph:
            images.extend(self._jsonld_images(graph, page_url))
        return images

    @staticmethod
    def _looks_like_media_url(value: str) -> bool:
        lower = value.lower()
        return lower.startswith(("http://", "https://", "/")) and any(
            token in lower for token in (".jpg", ".jpeg", ".png", ".webp", ".gif", "image", "photo", "avatar", "thumbnail")
        )

    def _download_binary(self, url: str, max_bytes: int) -> Tuple[Optional[bytes], str]:
        if not url:
            return None, ""

        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.download_timeout,
                stream=True,
            )
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()

            chunks = []
            total = 0
            for chunk in response.iter_content(chunk_size=64_000):
                if not chunk:
                    continue
                total += len(chunk)
                if total > max_bytes:
                    return None, content_type
                chunks.append(chunk)

            return b"".join(chunks), content_type
        except Exception:
            return None, ""

    def _download_image_bytes(self, image_url: str) -> Optional[bytes]:
        payload, content_type = self._download_binary(image_url, self.max_image_bytes)
        if content_type and "image" not in content_type:
            return None
        return payload

    def _download_video_bytes(self, video_url: str) -> Optional[bytes]:
        payload, content_type = self._download_binary(video_url, self.max_video_bytes)
        if content_type and "video" not in content_type and "octet-stream" not in content_type:
            return None
        return payload

    def _sample_video_frames(self, video_url: str) -> List[bytes]:
        payload = self._download_video_bytes(video_url)
        if not payload:
            return []

        frames: List[bytes] = []
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            tmp.write(payload)
            tmp.flush()
            capture = cv2.VideoCapture(tmp.name)
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            positions = [0, frame_count // 3, (frame_count * 2) // 3] if frame_count else [0, 30, 90]
            for pos in positions:
                capture.set(cv2.CAP_PROP_POS_FRAMES, pos)
                ok, frame = capture.read()
                if not ok or frame is None:
                    continue
                encoded_ok, encoded = cv2.imencode(".jpg", frame)
                if encoded_ok:
                    frames.append(encoded.tobytes())
            capture.release()
        return frames

    def _candidate_image_urls(self, item: Dict[str, Any]) -> List[str]:
        urls = []
        for key in ("image_url", "thumbnail", "original", "poster_url", "avatar_url"):
            value = item.get(key)
            if value:
                urls.append(value)
        page_url = item.get("url", "")
        if page_url:
            urls.extend(self.extract_page_images(page_url))
        return self._dedupe(urls)

    def _reject(self, item: Dict[str, Any], reason: str, image_url: Optional[str] = None, detail: Optional[str] = None) -> Dict[str, Any]:
        return {
            "url": item.get("url", ""),
            "title": item.get("title", "Public Web Match"),
            "source": item.get("source", "Web"),
            "provider": item.get("provider", item.get("provider_name", "Search")),
            "image_url": image_url,
            "reason": reason,
            "detail": detail,
        }

    def _evaluate_image(
        self,
        item: Dict[str, Any],
        image_url: str,
        image_bytes: bytes,
        input_embedding: List[float],
        input_embedding_model: Optional[str],
        input_crop_b64: Optional[str],
        strict_face_match: bool,
        raw_rank: int,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        try:
            candidate_img = self.detector.load_image(image_bytes)
            det_res = self.detector.detect_faces(candidate_img)
            if not det_res.get("face_detected"):
                return None, self._reject(item, "no_detectable_face", image_url)

            emb_res = self.encoder.generate_embedding_from_landmarks(
                candidate_img,
                det_res.get("primary_landmarks"),
            )
            candidate_model = emb_res.get("model")
            if strict_face_match and (
                not self._is_arcface_model(input_embedding_model)
                or not self._is_arcface_model(candidate_model)
            ):
                return None, self._reject(
                    item,
                    "arcface_required",
                    image_url,
                    "Strict matching requires InsightFace/ArcFace embeddings for input and candidate.",
                )

            candidate_similarity = self.matcher.cosine_similarity(
                input_embedding,
                emb_res["embedding"],
            )
        except Exception as exc:
            return None, self._reject(item, "candidate_processing_failed", image_url, str(exc))

        match_eval = self.matcher.evaluate_match(
            candidate_similarity,
            model_family="arcface" if self._is_arcface_model(candidate_model) else "fallback",
        )
        if not match_eval["is_match"]:
            return None, self._reject(
                item,
                "low_similarity",
                image_url,
                f"{match_eval['similarity_percent']}% similarity",
            )

        discovered_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return {
            "rank": raw_rank,
            "url": item.get("url", ""),
            "title": item.get("title", "Public Web Match"),
            "source": item.get("source", "Web"),
            "snippet": item.get("snippet", ""),
            "image_url": image_url,
            "candidate_face_preview": det_res.get("primary_crop_b64") or input_crop_b64,
            "similarity": match_eval["similarity"],
            "similarity_percent": match_eval["similarity_percent"],
            "match_category": match_eval["category"],
            "match_label": match_eval["label"],
            "is_match": True,
            "color": match_eval["color"],
            "candidate_faces_found": det_res.get("faces_found", 0),
            "candidate_detection_method": det_res.get("detection_method"),
            "match_evidence": "arcface_cosine_similarity_of_face_embeddings"
            if strict_face_match
            else "cosine_similarity_of_face_embeddings",
            "embedding_model": candidate_model,
            "provider": item.get("provider", item.get("provider_name", "Search")),
            "discovered_at": discovered_at,
        }, None

    def process_candidates_with_rejections(
        self,
        raw_results: List[Dict[str, Any]],
        input_embedding: List[float],
        input_crop_b64: Optional[str] = None,
        input_embedding_model: Optional[str] = None,
        strict_face_match: bool = True,
    ) -> Dict[str, Any]:
        """Download candidate media, verify faces, and keep rejected evidence."""
        verified_candidates: List[Dict[str, Any]] = []
        rejected_candidates: List[Dict[str, Any]] = []

        if strict_face_match and not self._is_arcface_model(input_embedding_model):
            return {
                "verified_candidates": [],
                "rejected_candidates": [
                    {
                        "url": "",
                        "title": "Input embedding",
                        "source": "FaceTrace",
                        "provider": "FaceEncoder",
                        "image_url": None,
                        "reason": "arcface_required",
                        "detail": "Input face was not encoded with InsightFace/ArcFace.",
                    }
                ],
            }

        for idx, item in enumerate(raw_results[: self.max_candidates]):
            image_urls = self._candidate_image_urls(item)
            if not image_urls:
                rejected_candidates.append(self._reject(item, "no_candidate_image"))
                continue

            candidate_matched_or_processed = False
            for image_url in image_urls[: self.max_images_per_page]:
                lower_url = image_url.lower()
                media_payloads: List[Tuple[str, bytes]] = []
                if any(ext in lower_url for ext in (".mp4", ".mov", ".webm", ".m3u8")):
                    media_payloads.extend((image_url, frame) for frame in self._sample_video_frames(image_url))
                    if not media_payloads:
                        rejected_candidates.append(self._reject(item, "blocked_or_unusable_video", image_url))
                    continue

                image_bytes = self._download_image_bytes(image_url)
                if image_bytes:
                    media_payloads.append((image_url, image_bytes))
                else:
                    rejected_candidates.append(self._reject(item, "blocked_or_unusable_image", image_url))
                    continue

                for matched_image_url, payload in media_payloads:
                    candidate, rejected = self._evaluate_image(
                        item=item,
                        image_url=matched_image_url,
                        image_bytes=payload,
                        input_embedding=input_embedding,
                        input_embedding_model=input_embedding_model,
                        input_crop_b64=input_crop_b64,
                        strict_face_match=strict_face_match,
                        raw_rank=idx + 1,
                    )
                    candidate_matched_or_processed = True
                    if candidate:
                        verified_candidates.append(candidate)
                        break
                    if rejected:
                        rejected_candidates.append(rejected)
                if verified_candidates and verified_candidates[-1].get("url") == item.get("url"):
                    break

            if not candidate_matched_or_processed and image_urls:
                rejected_candidates.append(self._reject(item, "no_processable_media", image_urls[0]))

        verified_candidates.sort(key=lambda c: c["similarity"], reverse=True)
        for i, cand in enumerate(verified_candidates):
            cand["rank"] = i + 1

        return {
            "verified_candidates": verified_candidates,
            "rejected_candidates": rejected_candidates,
        }

    def process_candidates(
        self,
        raw_results: List[Dict[str, Any]],
        input_embedding: List[float],
        input_crop_b64: Optional[str] = None,
        input_embedding_model: Optional[str] = None,
        strict_face_match: bool = False,
    ) -> List[Dict[str, Any]]:
        """Backward-compatible candidate processing API."""
        return self.process_candidates_with_rejections(
            raw_results=raw_results,
            input_embedding=input_embedding,
            input_crop_b64=input_crop_b64,
            input_embedding_model=input_embedding_model,
            strict_face_match=strict_face_match,
        )["verified_candidates"]

    def extract_canonical_metadata(self, best_match: Dict[str, Any]) -> Dict[str, Any]:
        """Extract minimal canonical metadata to be cryptographically hashed."""
        return {
            "source": best_match.get("source", "Web"),
            "provider": best_match.get("provider", "Search"),
            "url": best_match.get("url", ""),
            "title": best_match.get("title", ""),
            "caption": best_match.get("snippet", ""),
            "image_url": best_match.get("image_url", ""),
            "similarity_percent": best_match.get("similarity_percent"),
            "match_category": best_match.get("match_category"),
            "embedding_model": best_match.get("embedding_model"),
            "match_evidence": best_match.get("match_evidence"),
            "coverage_note": self.coverage_note,
            "discovered_at": best_match.get("discovered_at", datetime.datetime.now(datetime.timezone.utc).isoformat()),
        }

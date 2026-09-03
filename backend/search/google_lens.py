"""SerpApi Google Lens implementation."""

import io
import os
from typing import Any, Dict, List, Optional

import requests
from PIL import Image

from backend.search.base import ReverseImageSearcher


class GoogleLensSearcher(ReverseImageSearcher):
    """Executes reverse search via SerpApi Google Lens engine."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self.upload_url = "https://serpapi.com/image"
        self.search_url = "https://serpapi.com/search.json"

    def _compress_for_upload(self, image_bytes: bytes) -> bytes:
        """SerpApi Image API accepts files up to 500 KB."""
        if len(image_bytes) <= 500_000:
            return image_bytes

        with Image.open(io.BytesIO(image_bytes)) as img:
            img = img.convert("RGB")
            for quality in (88, 78, 68, 58, 48):
                out = io.BytesIO()
                img.save(out, format="JPEG", quality=quality, optimize=True)
                payload = out.getvalue()
                if len(payload) <= 500_000:
                    return payload

            img.thumbnail((900, 900))
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=65, optimize=True)
            return out.getvalue()

    def _upload_image(self, image_bytes: bytes, filename: str) -> str:
        upload_bytes = self._compress_for_upload(image_bytes)
        response = requests.post(
            self.upload_url,
            files={"image": (filename, upload_bytes, "image/jpeg")},
            data={"api_key": self.api_key},
            timeout=30,
        )
        response.raise_for_status()
        image_id = response.json().get("image_id")
        if not image_id:
            raise RuntimeError("SerpApi image upload succeeded without returning image_id.")
        return image_id

    def search(
        self,
        image_bytes: bytes,
        filename: str = "query.jpg",
        search_query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY is required for SerpApi Google Lens search.")

        image_id = self._upload_image(image_bytes, filename)
        params = {
            "engine": "google_lens",
            "image_id": image_id,
            "type": "visual_matches",
            "api_key": self.api_key,
        }
        if search_query:
            params["q"] = search_query

        response = requests.get(self.search_url, params=params, timeout=45)
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            raise RuntimeError(data["error"])

        results = []
        visual_matches = data.get("visual_matches", [])
        for item in visual_matches:
            url = item.get("link") or item.get("source_url") or ""
            if not url:
                continue
            results.append({
                "position": item.get("position"),
                "url": url,
                "title": item.get("title") or "Visual Match",
                "source": item.get("source") or "Google Lens",
                "image_url": item.get("thumbnail") or item.get("original") or item.get("image") or "",
                "snippet": item.get("snippet") or item.get("title") or "",
                "serpapi_image_id": image_id,
            })

        return results

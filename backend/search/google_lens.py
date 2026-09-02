"""SerpApi Google Lens implementation."""

import os
import requests
from typing import List, Dict, Any
from backend.search.base import ReverseImageSearcher


class GoogleLensSearcher(ReverseImageSearcher):
    """Executes reverse search via SerpApi Google Lens engine."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY") or os.getenv("SEARCH_API_KEY")

    def search(self, image_bytes: bytes, filename: str = "query.jpg") -> List[Dict[str, Any]]:
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY or SEARCH_API_KEY required for GoogleLensSearcher.")

        # SerpApi requires an uploaded image or public URL
        # For direct upload, SerpApi supports direct multipart upload or binary query
        url = "https://serpapi.com/search"
        files = {"image": (filename, image_bytes, "image/jpeg")}
        params = {
            "engine": "google_lens",
            "api_key": self.api_key,
        }

        response = requests.post(url, params=params, files=files, timeout=20)
        response.raise_for_status()
        data = response.json()

        results = []
        visual_matches = data.get("visual_matches", [])
        for item in visual_matches:
            results.append({
                "url": item.get("link") or item.get("source_url") or "",
                "title": item.get("title") or "Visual Match",
                "source": item.get("source") or "Google Lens",
                "image_url": item.get("thumbnail") or item.get("original") or "",
                "snippet": item.get("snippet") or item.get("title") or "",
            })

        return results

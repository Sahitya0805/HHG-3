"""Public web/profile/video discovery backed by SerpApi Google Search."""

import os
from typing import Any, Dict, List, Optional

import requests

from backend.search.base import ReverseImageSearcher


class PublicWebSearcher(ReverseImageSearcher):
    """
    Searches public/indexed profile and post surfaces.

    This is not a face-search provider by itself. It uses the optional user hint
    to discover likely public pages, then ResultParser verifies faces locally.
    """

    PLATFORM_QUERIES = [
        ("GitHub", "site:github.com"),
        ("LinkedIn", "site:linkedin.com/in OR site:linkedin.com/posts"),
        ("Instagram", "site:instagram.com/p OR site:instagram.com/reel OR site:instagram.com"),
        ("X (Twitter)", "site:x.com OR site:twitter.com"),
        ("Facebook", "site:facebook.com/posts OR site:facebook.com/profile.php OR site:facebook.com"),
        ("YouTube", "site:youtube.com/watch OR site:youtube.com/shorts OR site:youtu.be"),
        ("TikTok", "site:tiktok.com/@"),
        ("Personal Sites", "-site:facebook.com -site:instagram.com -site:x.com -site:twitter.com -site:linkedin.com -site:youtube.com -site:tiktok.com -site:github.com"),
    ]

    VIDEO_TERMS = {
        "YouTube": "video OR shorts",
        "TikTok": "video",
        "Instagram": "reel OR post",
        "Facebook": "video OR post",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self.search_url = "https://serpapi.com/search.json"

    def search(
        self,
        image_bytes: bytes,
        filename: str = "query.jpg",
        search_query: Optional[str] = None,
        include_videos: bool = True,
        max_sources: int = 8,
        max_candidates_per_source: int = 5,
    ) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY is required for public web search.")

        hint = (search_query or "").strip()
        if not hint:
            return []

        results: List[Dict[str, Any]] = []
        selected_queries = self.PLATFORM_QUERIES[: max(1, max_sources)]

        for source, site_query in selected_queries:
            query = f'"{hint}" ({site_query})'
            if include_videos and source in self.VIDEO_TERMS:
                query = f"{query} {self.VIDEO_TERMS[source]}"

            params = {
                "engine": "google",
                "q": query,
                "api_key": self.api_key,
                "num": max(1, min(max_candidates_per_source, 10)),
            }
            response = requests.get(self.search_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get("error"):
                raise RuntimeError(data["error"])

            organic = data.get("organic_results", [])
            inline_images = data.get("inline_images", [])

            for item in organic[:max_candidates_per_source]:
                url = item.get("link") or ""
                if not url:
                    continue
                results.append({
                    "url": url,
                    "title": item.get("title") or "Public Web Result",
                    "source": source,
                    "image_url": item.get("thumbnail") or "",
                    "snippet": item.get("snippet") or "",
                    "provider": "SerpApi Google Search",
                    "search_query": query,
                })

            for item in inline_images[: max(0, max_candidates_per_source - len(organic))]:
                original = item.get("original") or item.get("source") or item.get("link") or ""
                if not original:
                    continue
                results.append({
                    "url": item.get("source") or original,
                    "title": item.get("title") or "Public Image Result",
                    "source": source,
                    "image_url": original,
                    "snippet": item.get("snippet") or "",
                    "provider": "SerpApi Google Search Images",
                    "search_query": query,
                })

        return results


# Backward-compatible name used by older tests/imports.
LiveWebSearcher = PublicWebSearcher

from __future__ import annotations
from typing import List, Dict, Any, Optional
import os

# Optional deps
try:
    from googleapiclient.discovery import build as _build  # type: ignore

    _HAS_YT_API = True
except Exception:
    _HAS_YT_API = False
    _build = None  # type: ignore

try:
    # Captions (optional)
    from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore

    _HAS_TRANSCRIPTS = True
except Exception:
    _HAS_TRANSCRIPTS = False
    YouTubeTranscriptApi = None  # type: ignore


class YouTubeSource:
    """
    YouTube search + captions (stub-safe).
    - Uses googleapiclient if available and YOUTUBE_API_KEY set.
    - Falls back to stub metadata if offline/no key.
    - Captions via youtube_transcript_api if available.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (
            api_key or os.getenv("YOUTUBE_API_KEY") or os.getenv("YT_API_KEY")
        )
        self.client = None
        if _HAS_YT_API and self.api_key:
            try:
                self.client = _build("youtube", "v3", developerKey=self.api_key)
            except Exception:
                self.client = None

    # ---- Search ----
    def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        order: str = "relevance",
        relevance_language: Optional[str] = "en",
        region_code: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return a list of {video_id,title,description,channel,published_at,url}.
        """
        if self.client:
            params: Dict[str, Any] = dict(
                part="id,snippet",
                q=query,
                type="video",
                maxResults=max(1, min(max_results, 50)),
                order=order,
            )
            if relevance_language:
                params["relevanceLanguage"] = relevance_language
            if region_code:
                params["regionCode"] = region_code

            req = self.client.search().list(**params)
            data = req.execute()
            out: List[Dict[str, Any]] = []
            for item in data.get("items", []):
                vid = item["id"]["videoId"]
                sn = item["snippet"]
                out.append(
                    {
                        "video_id": vid,
                        "title": sn.get("title", ""),
                        "description": sn.get("description", ""),
                        "channel": sn.get("channelTitle", ""),
                        "published_at": sn.get("publishedAt", ""),
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "source_type": "youtube",
                    }
                )
            return out

        # Stub fallback
        if not (query or "").strip():
            return []
        return [
            {
                "video_id": "stub123",
                "title": f"[stub] {query} overview",
                "description": "Stub description of a relevant civil engineering topic.",
                "channel": "StubChannel",
                "published_at": "2000-01-01T00:00:00Z",
                "url": "https://www.youtube.com/watch?v=stub123",
                "source_type": "youtube",
            }
        ]

    # ---- Captions ----
    def captions(self, video_id: str, languages: Optional[List[str]] = None) -> str:
        """
        Return plain caption text if available; else empty string.
        """
        languages = languages or ["en", "en-US"]
        if _HAS_TRANSCRIPTS:
            # Try requested languages first
            for lang in languages:
                try:
                    segs = YouTubeTranscriptApi.get_transcript(
                        video_id, languages=[lang]
                    )
                    return " ".join(s.get("text", "") for s in segs)
                except Exception:
                    pass
            # Any transcript fallback
            try:
                segs = YouTubeTranscriptApi.get_transcript(video_id)
                return " ".join(s.get("text", "") for s in segs)
            except Exception:
                return ""
        return ""

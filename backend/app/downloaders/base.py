from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class VideoQualityOption:
    def __init__(
        self,
        quality_label: str,
        download_url: str,
        has_watermark: bool = False,
        bitrate: int = 0,
        width: int = 0,
        height: int = 0,
        format_ext: str = "mp4",
        filesize: Optional[int] = None
    ):
        self.quality_label = quality_label
        self.download_url = download_url
        self.has_watermark = has_watermark
        self.bitrate = bitrate
        self.width = width
        self.height = height
        self.format_ext = format_ext
        self.filesize = filesize

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quality_label": self.quality_label,
            "download_url": self.download_url,
            "has_watermark": self.has_watermark,
            "bitrate": self.bitrate,
            "width": self.width,
            "height": self.height,
            "format": self.format_ext,
            "filesize": self.filesize
        }

class VideoSourceInfo:
    def __init__(
        self,
        video_id: str,
        title: str,
        author: str,
        cover_url: str,
        qualities: List[VideoQualityOption],
        provider_name: str,
        original_url: str = ""
    ):
        self.video_id = video_id
        self.title = title
        self.author = author
        self.cover_url = cover_url
        self.qualities = qualities
        self.provider_name = provider_name
        self.original_url = original_url

    @property
    def best_quality(self) -> Optional[VideoQualityOption]:
        """
        Picks highest quality:
        1. Prioritize no-watermark options.
        2. Prioritize higher resolution (height/width) then bitrate.
        """
        if not self.qualities:
            return None

        no_wm = [q for q in self.qualities if not q.has_watermark]
        candidate_pool = no_wm if no_wm else self.qualities

        def _sort_key(q: VideoQualityOption):
            # Sort by height or label (e.g. 1080 > 720 > 540)
            res_score = max(q.height, q.width)
            if res_score == 0:
                if "1080" in q.quality_label:
                    res_score = 1080
                elif "720" in q.quality_label or "hd" in q.quality_label.lower():
                    res_score = 720
                elif "540" in q.quality_label:
                    res_score = 540
                else:
                    res_score = 480
            return (res_score, q.bitrate)

        return max(candidate_pool, key=_sort_key)

    def to_dict(self) -> Dict[str, Any]:
        best = self.best_quality
        return {
            "video_id": self.video_id,
            "title": self.title,
            "author": self.author,
            "cover_url": self.cover_url,
            "original_url": self.original_url,
            "provider_name": self.provider_name,
            "best_quality": best.to_dict() if best else None,
            "qualities": [q.to_dict() for q in self.qualities]
        }

class BaseDownloadProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def get_video_source(self, url_or_id: str) -> Optional[VideoSourceInfo]:
        """Resolves direct download stream URLs for a given Douyin video URL or ID."""
        pass

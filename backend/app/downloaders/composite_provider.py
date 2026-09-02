import time
import logging
from typing import Optional, Dict, Tuple
from .base import BaseDownloadProvider, VideoSourceInfo
from .douyin_direct_provider import DouyinDirectProvider
from .snaptiktok_provider import SnapTikTokProvider

logger = logging.getLogger("CompositeDownloadProvider")

class CompositeDownloadProvider(BaseDownloadProvider):
    def __init__(self):
        self.providers = [
            DouyinDirectProvider(),
            SnapTikTokProvider()
        ]
        # In-memory cache for download sources: {url_or_id: (VideoSourceInfo, expire_timestamp)}
        self._source_cache: Dict[str, Tuple[VideoSourceInfo, float]] = {}
        self._cache_ttl_seconds: int = 1800  # 30 minutes

    @property
    def name(self) -> str:
        return "composite_highest_quality"

    async def get_video_source(self, url_or_id: str) -> Optional[VideoSourceInfo]:
        cache_key = url_or_id.strip()
        if cache_key in self._source_cache:
            info, exp = self._source_cache[cache_key]
            if time.time() < exp:
                return info
            else:
                del self._source_cache[cache_key]

        # Try providers in order
        for provider in self.providers:
            try:
                res = await provider.get_video_source(url_or_id)
                if res and res.qualities and res.best_quality:
                    self._source_cache[cache_key] = (res, time.time() + self._cache_ttl_seconds)
                    return res
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed for {url_or_id}: {e}")

        # Fallback to direct resolution
        direct = DouyinDirectProvider()
        res = await direct.get_video_source(url_or_id)
        if res:
            self._source_cache[cache_key] = (res, time.time() + self._cache_ttl_seconds)
        return res

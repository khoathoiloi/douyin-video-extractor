from .base import BaseDownloadProvider
from .douyin_direct_provider import DouyinDirectProvider
from .snaptiktok_provider import SnapTikTokProvider
from .composite_provider import CompositeDownloadProvider

_download_provider_instance = None

def get_download_provider(provider_type: str = "composite") -> BaseDownloadProvider:
    global _download_provider_instance
    if _download_provider_instance is None:
        if provider_type == "snaptiktok":
            _download_provider_instance = SnapTikTokProvider()
        elif provider_type == "direct":
            _download_provider_instance = DouyinDirectProvider()
        else:
            _download_provider_instance = CompositeDownloadProvider()
    return _download_provider_instance

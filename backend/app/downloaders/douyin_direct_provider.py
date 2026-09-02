import re
import aiohttp
import logging
from typing import Optional, List
from .base import BaseDownloadProvider, VideoSourceInfo, VideoQualityOption
from ..core.config import settings

logger = logging.getLogger("DouyinDirectProvider")

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

class DouyinDirectProvider(BaseDownloadProvider):
    @property
    def name(self) -> str:
        return "douyin_direct_hd"

    @staticmethod
    def extract_id(url_or_id: str) -> str:
        if not url_or_id:
            return ""
        if url_or_id.isdigit() and len(url_or_id) >= 15:
            return url_or_id
        m = re.search(r"video/(\d+)", url_or_id)
        if m:
            return m.group(1)
        m2 = re.search(r"(\d{18,20})", url_or_id)
        if m2:
            return m2.group(1)
        return url_or_id.strip()

    async def get_video_source(self, url_or_id: str) -> Optional[VideoSourceInfo]:
        video_id = self.extract_id(url_or_id)
        if not video_id:
            return None

        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Referer": "https://www.douyin.com/",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        if settings.DOUYIN_COOKIE:
            headers["Cookie"] = settings.DOUYIN_COOKIE

        qualities: List[VideoQualityOption] = []
        title = f"Douyin_{video_id}"
        author = "Douyin Creator"
        cover_url = ""

        async with aiohttp.ClientSession(headers=headers) as session:
            # 1. Try iesdouyin / web item detail API
            api_url = f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}"
            try:
                async with session.get(api_url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        item_list = data.get("item_list", [])
                        if item_list:
                            item = item_list[0]
                            title = item.get("desc", title)
                            author = item.get("author", {}).get("nickname", author)
                            cover_url = item.get("video", {}).get("cover", {}).get("url_list", [""])[0]

                            # Play addr with wm replace
                            play_list = item.get("video", {}).get("play_addr", {}).get("url_list", [])
                            for p_url in play_list:
                                # Replace playwm with play for no watermark
                                no_wm_url = p_url.replace("playwm", "play")
                                qualities.append(VideoQualityOption(
                                    quality_label="1080p HD (No Watermark)",
                                    download_url=no_wm_url,
                                    has_watermark=False,
                                    height=1080
                                ))
            except Exception as e:
                logger.warning(f"Direct API iteminfo notice for {video_id}: {e}")

            # 2. Add standard direct stream play URLs as fallback options
            hd_play_url = f"https://aweme.snssdk.com/aweme/v1/play/?video_id={video_id}&ratio=1080p&line=0"
            qualities.append(VideoQualityOption(
                quality_label="1080p Stream (High Bitrate)",
                download_url=hd_play_url,
                has_watermark=False,
                height=1080
            ))

            sd_play_url = f"https://aweme.snssdk.com/aweme/v1/play/?video_id={video_id}&ratio=720p&line=0"
            qualities.append(VideoQualityOption(
                quality_label="720p HD Stream",
                download_url=sd_play_url,
                has_watermark=False,
                height=720
            ))

        return VideoSourceInfo(
            video_id=video_id,
            title=title,
            author=author,
            cover_url=cover_url,
            qualities=qualities,
            provider_name=self.name,
            original_url=f"https://www.douyin.com/video/{video_id}"
        )

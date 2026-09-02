import re
import aiohttp
import logging
from typing import Optional, List
from bs4 import BeautifulSoup
from .base import BaseDownloadProvider, VideoSourceInfo, VideoQualityOption

logger = logging.getLogger("SnapTikTokProvider")

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

class SnapTikTokProvider(BaseDownloadProvider):
    @property
    def name(self) -> str:
        return "snaptiktok"

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
        target_url = url_or_id if url_or_id.startswith("http") else f"https://www.douyin.com/video/{video_id}"

        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Referer": "https://snaptiktok.to/",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest"
        }

        qualities: List[VideoQualityOption] = []
        title = f"Douyin_{video_id}"
        author = "Douyin Creator"
        cover_url = ""

        try:
            timeout = aiohttp.ClientTimeout(total=8)
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                # SnapTikTok resolve endpoint
                api_url = "https://snaptiktok.to/action.php"
                payload = {
                    "url": target_url,
                    "action": "post"
                }
                async with session.post(api_url, data=payload) as resp:
                    if resp.status == 200:
                        content_type = resp.headers.get("Content-Type", "")
                        if "json" in content_type:
                            data = await resp.json()
                            html_content = data.get("data", "") or data.get("html", "")
                        else:
                            html_content = await resp.text()

                        if html_content:
                            soup = BeautifulSoup(html_content, "html.parser")
                            # Extract title & author
                            title_tag = soup.find(["h3", "h4", "p", "div"], class_=re.compile(r"title|desc|text", re.I))
                            if title_tag:
                                title = title_tag.get_text(strip=True)

                            # Extract download links
                            links = soup.find_all("a", href=True)
                            for link in links:
                                href = link["href"]
                                text = link.get_text(strip=True)
                                if "download" in href.lower() or "snap" in href.lower() or "tik" in href.lower() or "video" in href.lower():
                                    is_hd = "hd" in text.lower() or "1080" in text or "gốc" in text.lower()
                                    no_wm = "no watermark" in text.lower() or "không logo" in text.lower() or not ("watermark" in text.lower())
                                    qualities.append(VideoQualityOption(
                                        quality_label=f"SnapTikTok {text or 'HD'}",
                                        download_url=href,
                                        has_watermark=not no_wm,
                                        height=1080 if is_hd else 720
                                    ))

                            # Extract thumbnail
                            img_tag = soup.find("img", src=True)
                            if img_tag:
                                cover_url = img_tag["src"]

        except Exception as e:
            logger.warning(f"SnapTikTok provider notice for {url_or_id}: {e}")

        if not qualities:
            return None

        return VideoSourceInfo(
            video_id=video_id,
            title=title,
            author=author,
            cover_url=cover_url,
            qualities=qualities,
            provider_name=self.name,
            original_url=target_url
        )

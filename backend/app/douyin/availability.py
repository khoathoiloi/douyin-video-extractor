import re
import time
import asyncio
import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import aiohttp

logger = logging.getLogger("DouyinAvailabilityChecker")

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

class VideoAvailabilityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    PRIVATE = "PRIVATE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"

class AvailabilityResult:
    def __init__(self, video_id: str, status: VideoAvailabilityStatus, reason: str = "", http_status: Optional[int] = None):
        self.video_id = video_id
        self.status = status
        self.reason = reason
        self.http_status = http_status
        self.checked_at = time.time()

    def is_usable(self) -> bool:
        """Only ACTIVE and UNKNOWN are kept. DELETED, PRIVATE, UNAVAILABLE are discarded."""
        return self.status in (VideoAvailabilityStatus.ACTIVE, VideoAvailabilityStatus.UNKNOWN)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "video_id": self.video_id,
            "status": self.status.value,
            "reason": self.reason,
            "http_status": self.http_status,
            "checked_at": self.checked_at
        }

class DouyinAvailabilityChecker:
    # Dead signals
    DELETED_PATTERNS = [
        "你浏览的视频不是有效视频",
        "不是有效视频",
        "非有效视频",
        "抱歉，作品不见了",
        "作品不存在",
        "作品已删除",
        "作品已被删除",
        "该视频已被删除",
        "该作品已被删除",
        "视频不存在",
        "内容不存在",
        "暂无此视频",
        "该视频暂不可用",
        "视频不可用",
        "作品不可用",
        "aweme_not_exists",
        "aweme not found",
    ]

    # Private signals
    PRIVATE_PATTERNS = [
        "仅自己可见",
        "权限限制",
        "该视频已被设为私密",
        "私密作品",
        "创作者已将作品设为私密",
        "private_aweme",
    ]

    # Unavailable / banned / under review signals
    UNAVAILABLE_PATTERNS = [
        "无法观看",
        "视频审核中",
        "该作品正在审核中",
        "作品已被封禁",
        "因违规无法查看",
        "违规下架",
    ]

    # Temporary rate-limit / server error / anti-bot signals (Must remain UNKNOWN, NEVER DELETED)
    TEMPORARY_PATTERNS = [
        "服务器出现问题",
        "请稍后重试",
        "系统繁忙",
        "访问过于频繁",
        "网络开小差",
        "环境异常",
        "verify",
        "captcha"
    ]

    # In-memory TTL cache: {video_id: (AvailabilityResult, expire_timestamp)}
    _cache: Dict[str, Tuple[AvailabilityResult, float]] = {}
    _cache_ttl_seconds: int = 3600  # 1 hour

    @classmethod
    def get_cached_status(cls, video_id: str) -> Optional[AvailabilityResult]:
        if not video_id:
            return None
        cached = cls._cache.get(video_id)
        if cached:
            result, expire_at = cached
            if time.time() < expire_at:
                return result
            else:
                del cls._cache[video_id]
        return None

    @classmethod
    def set_cached_status(cls, video_id: str, result: AvailabilityResult):
        if not video_id:
            return
        cls._cache[video_id] = (result, time.time() + cls._cache_ttl_seconds)

    @classmethod
    def extract_video_id(cls, raw: str) -> str:
        if not raw:
            return ""
        # If pure digit string
        if raw.isdigit() and len(raw) >= 15:
            return raw
        # Extract from URL
        m = re.search(r"video/(\d+)", raw)
        if m:
            return m.group(1)
        m2 = re.search(r"(\d{18,20})", raw)
        if m2:
            return m2.group(1)
        return raw.strip()

    @classmethod
    async def check_single_video(
        cls,
        video_identifier: str,
        session: Optional[aiohttp.ClientSession] = None,
        cookie: str = "",
        timeout_seconds: float = 3.0
    ) -> AvailabilityResult:
        video_id = cls.extract_video_id(video_identifier)
        if not video_id:
            return AvailabilityResult(video_identifier, VideoAvailabilityStatus.UNKNOWN, "Invalid identifier")

        # Check cache first
        cached = cls.get_cached_status(video_id)
        if cached:
            return cached

        # Construct target URLs to check
        url = f"https://www.douyin.com/video/{video_id}"
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Referer": "https://www.douyin.com/",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }
        if cookie:
            headers["Cookie"] = cookie

        should_close_session = False
        if session is None:
            timeout = aiohttp.ClientTimeout(total=timeout_seconds, connect=1.5)
            session = aiohttp.ClientSession(headers=headers, timeout=timeout)
            should_close_session = True

        result = AvailabilityResult(video_id, VideoAvailabilityStatus.UNKNOWN)

        try:
            # 1. Perform lightweight GET/HEAD with redirects
            async with session.get(url, allow_redirects=True, timeout=timeout_seconds) as resp:
                result.http_status = resp.status
                final_url = str(resp.url)

                if resp.status == 404:
                    result.status = VideoAvailabilityStatus.DELETED
                    result.reason = "HTTP 404 Video Not Found"
                    cls.set_cached_status(video_id, result)
                    return result

                # Read response text for pattern matching
                try:
                    text = await resp.text(errors="ignore")
                except Exception:
                    text = ""

                # Check for rate limit / Captcha / 5xx -> NEVER mark as dead, keep as UNKNOWN
                if resp.status in (429, 403) or "verify" in final_url or "captcha" in final_url or resp.status >= 500:
                    result.status = VideoAvailabilityStatus.UNKNOWN
                    result.reason = f"Temporary status {resp.status} / Verification page"
                    return result

                # Check for temporary server anti-bot text ('服务器出现问题', '请稍后重试', etc.)
                for p in cls.TEMPORARY_PATTERNS:
                    if p in text:
                        result.status = VideoAvailabilityStatus.UNKNOWN
                        result.reason = f"Temporary Douyin server message: {p}"
                        return result

                # Check Deleted Patterns
                for p in cls.DELETED_PATTERNS:
                    if p in text:
                        result.status = VideoAvailabilityStatus.DELETED
                        result.reason = f"Matched deleted signal: {p}"
                        cls.set_cached_status(video_id, result)
                        return result

                # Check Private Patterns
                for p in cls.PRIVATE_PATTERNS:
                    if p in text:
                        result.status = VideoAvailabilityStatus.PRIVATE
                        result.reason = f"Matched private signal: {p}"
                        cls.set_cached_status(video_id, result)
                        return result

                # Check Unavailable Patterns
                for p in cls.UNAVAILABLE_PATTERNS:
                    if p in text:
                        result.status = VideoAvailabilityStatus.UNAVAILABLE
                        result.reason = f"Matched unavailable signal: {p}"
                        cls.set_cached_status(video_id, result)
                        return result

                # If status 200 and has video details or og:title / scripts, mark ACTIVE
                if resp.status == 200:
                    if "video" in text or "aweme" in text or "RENDER_DATA" in text or "<title>" in text:
                        result.status = VideoAvailabilityStatus.ACTIVE
                        result.reason = "Video page loaded successfully and active"
                    else:
                        result.status = VideoAvailabilityStatus.UNKNOWN
                        result.reason = "Page response unclear, default to UNKNOWN"
                else:
                    result.status = VideoAvailabilityStatus.UNKNOWN
                    result.reason = f"Non-200 HTTP status: {resp.status}"

        except asyncio.TimeoutError:
            result.status = VideoAvailabilityStatus.UNKNOWN
            result.reason = "Timeout during availability check"
        except aiohttp.ClientError as e:
            result.status = VideoAvailabilityStatus.UNKNOWN
            result.reason = f"Network error: {str(e)}"
        except Exception as e:
            result.status = VideoAvailabilityStatus.UNKNOWN
            result.reason = f"Unexpected error: {str(e)}"
        finally:
            if should_close_session:
                await session.close()

        # Cache valid determinations
        if result.status != VideoAvailabilityStatus.UNKNOWN:
            cls.set_cached_status(video_id, result)

        return result

    @classmethod
    async def filter_candidates(
        cls,
        candidates: List[Dict[str, Any]],
        max_concurrency: int = 10,
        cookie: str = "",
        timeout_seconds: float = 3.0
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filters a list of candidate dictionaries.
        Returns: (active_and_unknown_candidates, removed_dead_or_private_candidates)
        """
        if not candidates:
            return [], []

        semaphore = asyncio.Semaphore(max_concurrency)
        timeout = aiohttp.ClientTimeout(total=timeout_seconds, connect=1.5)
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Referer": "https://www.douyin.com/",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        if cookie:
            headers["Cookie"] = cookie

        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async def _check_item(c: Dict[str, Any]) -> Tuple[Dict[str, Any], AvailabilityResult]:
                vid = c.get("remote_video_id") or c.get("video_id") or c.get("url", "")
                async with semaphore:
                    res = await cls.check_single_video(vid, session=session, cookie=cookie, timeout_seconds=timeout_seconds)
                    return c, res

            tasks = [_check_item(c) for c in candidates]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        kept: List[Dict[str, Any]] = []
        removed: List[Dict[str, Any]] = []

        for item in results:
            if isinstance(item, Exception):
                logger.warning(f"Error during candidate check: {item}")
                continue
            cand, avail = item
            cand["availability_status"] = avail.status.value
            cand["availability_reason"] = avail.reason

            if avail.is_usable():
                kept.append(cand)
            else:
                logger.info(f"Filtering out {avail.status.value} video {avail.video_id}: {avail.reason}")
                removed.append(cand)

        return kept, removed

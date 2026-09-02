"""
High-Performance In-Memory & File Cache Engine with TTL and Video Hash Fingerprinting
Optimizes Cloud Backend latency and reduces redundant AI API calls.
"""

import time
import hashlib
import threading
from typing import Dict, Any, Optional, List

class TTLCache:
    def __init__(self, default_ttl_seconds: int = 3600):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            if time.time() > entry["expires_at"]:
                del self._store[key]
                return None
            return entry["data"]

    def set(self, key: str, data: Any, ttl_seconds: Optional[int] = None):
        with self._lock:
            ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
            self._store[key] = {
                "data": data,
                "expires_at": time.time() + ttl
            }

    def delete(self, key: str):
        with self._lock:
            self._store.pop(key, None)

    def clear(self):
        with self._lock:
            self._store.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._store)


class VideoHashCache:
    """Computes SHA-256 fingerprint of video files to reuse multimodal AI analysis."""
    def __init__(self):
        self._cache = TTLCache(default_ttl_seconds=86400 * 7) # 7 days retention

    @staticmethod
    def compute_file_hash(file_path: str, sample_bytes: int = 1024 * 1024) -> str:
        h = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read head
                chunk = f.read(sample_bytes)
                h.update(chunk)
                # Read tail if large
                f.seek(0, 2)
                size = f.tell()
                if size > sample_bytes * 2:
                    f.seek(size - sample_bytes)
                    h.update(f.read(sample_bytes))
            return h.hexdigest()
        except Exception:
            return ""

    def get_analysis(self, file_hash: str) -> Optional[Dict[str, Any]]:
        if not file_hash:
            return None
        return self._cache.get(file_hash)

    def save_analysis(self, file_hash: str, analysis_data: Dict[str, Any]):
        if file_hash and analysis_data:
            self._cache.set(file_hash, analysis_data)


# Global Cache Singletons
query_cache = TTLCache(default_ttl_seconds=3600 * 12)     # 12 hours
search_cache = TTLCache(default_ttl_seconds=1800)         # 30 mins
video_hash_cache = VideoHashCache()


class SimpleRateLimiter:
    """Sliding-window IP rate limiter."""
    def __init__(self, max_requests: int = 120, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        with self._lock:
            timestamps = self.requests.get(ip, [])
            # Filter expired timestamps
            timestamps = [t for t in timestamps if now - t < self.window]
            if len(timestamps) >= self.max_requests:
                return False
            timestamps.append(now)
            self.requests[ip] = timestamps
            return True

rate_limiter = SimpleRateLimiter(max_requests=200, window_seconds=60)

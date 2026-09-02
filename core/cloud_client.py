"""
Core Module: Douyin Cloud API Client
Connects Desktop PC GUI to Cloud Backend API (FastAPI) via HTTPS / REST.
"""

import os
import time
import requests
from typing import Dict, Any, List, Optional, Callable

DEFAULT_SERVER_URL = "http://127.0.0.1:8000"

class DouyinCloudClient:
    def __init__(self, server_url: str = DEFAULT_SERVER_URL, timeout: int = 30):
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "DouyinDesktopClient/1.2 (Windows x64)",
            "Accept": "application/json"
        })

    def set_server_url(self, new_url: str):
        self.server_url = new_url.rstrip("/")

    def ping(self) -> Dict[str, Any]:
        """Tests connection to Cloud Server."""
        try:
            start_ts = time.time()
            resp = self.session.get(f"{self.server_url}/api/v1/settings", timeout=6)
            latency_ms = int((time.time() - start_ts) * 1000)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "connected": True,
                    "latency_ms": latency_ms,
                    "version": data.get("version", "1.0.0"),
                    "ai_provider": data.get("ai_provider", "gemini"),
                    "search_provider": data.get("douyin_search_provider", "live"),
                    "message": f"Kết nối Cloud Server thành công! ({latency_ms} ms)"
                }
            return {
                "connected": False,
                "error": f"Server phản hồi mã lỗi HTTP {resp.status_code}"
            }
        except Exception as e:
            return {
                "connected": False,
                "error": f"Không thể kết nối tới Cloud Server: {str(e)}"
            }

    def search_keyword(
        self,
        keyword: str,
        limit: int = 20,
        deep_search: bool = False,
        min_likes: int = 0
    ) -> Dict[str, Any]:
        """Performs search via Cloud API."""
        endpoint = f"{self.server_url}/api/v1/search"
        payload = {
            "query": keyword,
            "keyword": keyword,
            "limit": limit,
            "deep_search": deep_search,
            "min_likes": min_likes
        }
        try:
            resp = self.session.post(endpoint, json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                return {"success": True, "data": resp.json()}
            err_data = resp.json().get("detail", {})
            msg = err_data.get("error", {}).get("message") if isinstance(err_data, dict) else str(err_data)
            return {"success": False, "error": msg or f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": f"Lỗi kết nối mạng: {str(e)}"}

    def analyze_url(
        self,
        url: str,
        user_hint: str = "",
        deep_search: bool = False,
        progress_callback: Optional[Callable[[int, str, Optional[Dict[str, Any]]], None]] = None
    ) -> Dict[str, Any]:
        """Sends Douyin/TikTok URL to Cloud for multimodal analysis & waterfall search."""
        endpoint = f"{self.server_url}/api/v1/analyze/url"
        payload = {
            "url": url,
            "user_hint": user_hint,
            "deep_search": deep_search
        }
        try:
            resp = self.session.post(endpoint, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                err_data = resp.json().get("detail", {})
                msg = err_data.get("error", {}).get("message") if isinstance(err_data, dict) else str(err_data)
                return {"success": False, "error": msg or f"HTTP {resp.status_code}"}

            init_data = resp.json()
            job_id = init_data.get("job_id")
            if not job_id:
                return {"success": False, "error": "Không nhận được Job ID từ Cloud Server."}

            return self._poll_job_until_complete(job_id, progress_callback)
        except Exception as e:
            return {"success": False, "error": f"Lỗi phân tích URL: {str(e)}"}

    def analyze_video_file(
        self,
        file_path: str,
        user_hint: str = "",
        deep_search: bool = False,
        progress_callback: Optional[Callable[[int, str, Optional[Dict[str, Any]]], None]] = None
    ) -> Dict[str, Any]:
        """Uploads a local video to Cloud Server for background multimodal analysis."""
        endpoint = f"{self.server_url}/api/v1/analyze/video"
        if not os.path.exists(file_path):
            return {"success": False, "error": f"Tệp tin không tồn tại: {file_path}"}

        try:
            filename = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                files = {"file": (filename, f, "video/mp4")}
                data = {
                    "user_hint": user_hint,
                    "deep_search": str(deep_search).lower()
                }
                resp = self.session.post(endpoint, files=files, data=data, timeout=120)

            if resp.status_code != 200:
                err_data = resp.json().get("detail", {})
                msg = err_data.get("error", {}).get("message") if isinstance(err_data, dict) else str(err_data)
                return {"success": False, "error": msg or f"HTTP {resp.status_code}"}

            init_data = resp.json()
            job_id = init_data.get("job_id")
            if not job_id:
                return {"success": False, "error": "Không nhận được Job ID từ Cloud Server."}

            return self._poll_job_until_complete(job_id, progress_callback)
        except Exception as e:
            return {"success": False, "error": f"Lỗi upload video: {str(e)}"}

    def _poll_job_until_complete(
        self,
        job_id: str,
        progress_callback: Optional[Callable[[int, str, Optional[Dict[str, Any]]], None]] = None,
        max_wait_sec: int = 180
    ) -> Dict[str, Any]:
        """Polls Cloud Job status with live progress tracking."""
        start_ts = time.time()
        while time.time() - start_ts < max_wait_sec:
            try:
                resp = self.session.get(f"{self.server_url}/api/v1/jobs/{job_id}", timeout=10)
                if resp.status_code == 200:
                    job_data = resp.json()
                    stage = job_data.get("stage", "processing")
                    status = job_data.get("status", "pending")
                    pct = job_data.get("progress_percent", 0)
                    analysis = job_data.get("analysis")
                    queries = job_data.get("queries")

                    stage_names_vi = {
                        "queued": "Đang xếp hàng...",
                        "extracting_metadata": "Đang trích xuất thông tin video...",
                        "extracting_keyframes": "Đang phân tích khung hình AI...",
                        "transcribing_audio": "Đang trích xuất giọng nói (ASR)...",
                        "ocr_text": "Đang nhận diện chữ trên video (OCR)...",
                        "analyzing": "Đang phân tích ngữ nghĩa Multimodal AI...",
                        "generating_queries": "Đang sinh 20 từ khóa Douyin chuẩn SEO...",
                        "searching": "Đang quét video Douyin 4 tầng...",
                        "ranking": "Đang tính điểm & xếp hạng AI...",
                        "completed": "Hoàn tất!"
                    }
                    display_stage = stage_names_vi.get(stage, stage)

                    if progress_callback:
                        progress_callback(pct, display_stage, job_data)

                    if status == "completed":
                        # Fetch final ranked results
                        results_resp = self.session.get(f"{self.server_url}/api/v1/search/{job_id}/results?page=1&page_size=100", timeout=15)
                        results_data = results_resp.json() if results_resp.status_code == 200 else {}
                        return {
                            "success": True,
                            "job_id": job_id,
                            "analysis": analysis,
                            "queries": queries,
                            "results": results_data.get("results", []),
                            "total_results": results_data.get("total_results", 0)
                        }
                    elif status == "failed":
                        return {
                            "success": False,
                            "error": job_data.get("error_message") or "Phân tích thất bại trên Cloud Server."
                        }
            except Exception as e:
                pass

            time.sleep(1.5)

        return {"success": False, "error": "Hết thời gian chờ phản hồi từ Cloud Server (Timeout 180s)."}

    def get_history(self) -> List[Dict[str, Any]]:
        """Fetches history from Cloud."""
        try:
            resp = self.session.get(f"{self.server_url}/api/v1/history", timeout=10)
            if resp.status_code == 200:
                return resp.json().get("history", [])
        except Exception:
            pass
        return []

    def delete_history(self, video_id: str) -> bool:
        """Deletes history on Cloud."""
        try:
            resp = self.session.delete(f"{self.server_url}/api/v1/history/{video_id}", timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def get_cloud_settings(self) -> Dict[str, Any]:
        """Gets settings from Cloud."""
        try:
            resp = self.session.get(f"{self.server_url}/api/v1/settings", timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return {}

    def update_cloud_settings(self, payload: Dict[str, Any]) -> bool:
        """Updates settings on Cloud."""
        try:
            resp = self.session.put(f"{self.server_url}/api/v1/settings", json=payload, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

import os
import uuid
import time
import asyncio
import logging
import aiohttp
import aiofiles
from typing import Dict, Any, List, Optional
from ..core.config import settings
from ..downloaders.factory import get_download_provider
from ..drive.uploader import GoogleDriveUploader

logger = logging.getLogger("DownloadJobRunner")

class DownloadItemState:
    PENDING = "pending"
    FETCHING_SOURCE = "fetching_source"
    DOWNLOADING = "downloading"
    UPLOADING_DRIVE = "uploading_drive"
    COMPLETED = "completed"
    FAILED = "failed"

class DownloadJobManager:
    # In-memory jobs state: {job_id: job_dict}
    _jobs: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        return cls._jobs.get(job_id)

    @classmethod
    def create_job(
        cls,
        videos: List[Dict[str, Any]],
        upload_to_drive: bool = True,
        drive_folder: str = ""
    ) -> str:
        job_id = str(uuid.uuid4())
        items = []
        for idx, v in enumerate(videos):
            vid = v.get("video_id") or v.get("remote_video_id") or f"vid_{idx}"
            items.append({
                "video_id": vid,
                "url": v.get("url") or f"https://www.douyin.com/video/{vid}",
                "title": v.get("title") or f"Douyin_{vid}",
                "author": v.get("author") or "Douyin Creator",
                "cover_url": v.get("cover_url") or "",
                "status": DownloadItemState.PENDING,
                "progress": 0,
                "filename": "",
                "filesize": 0,
                "quality_label": "",
                "drive_link": "",
                "error_message": "",
                "retries": 0
            })

        cls._jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "upload_to_drive": upload_to_drive,
            "drive_folder": drive_folder or GoogleDriveUploader.get_default_target_folder(),
            "total_items": len(items),
            "completed_items": 0,
            "failed_items": 0,
            "progress_percent": 0,
            "created_at": time.time(),
            "items": items
        }
        return job_id

    @classmethod
    async def run_download_job(cls, job_id: str, max_concurrency: int = 3):
        job = cls.get_job(job_id)
        if not job:
            return

        job["status"] = "in_progress"
        semaphore = asyncio.Semaphore(max_concurrency)
        provider = get_download_provider()
        drive_uploader = GoogleDriveUploader()

        download_tmp_dir = os.path.join(settings.UPLOAD_DIR, "downloads_temp")
        os.makedirs(download_tmp_dir, exist_ok=True)

        async def _process_single_item(item: Dict[str, Any]):
            async with semaphore:
                try:
                    # Step 1: Fetch source
                    item["status"] = DownloadItemState.FETCHING_SOURCE
                    item["progress"] = 15
                    cls._update_overall_progress(job)

                    source_info = await provider.get_video_source(item["url"])
                    if not source_info or not source_info.best_quality:
                        raise ValueError("Không thể lấy luồng video hợp lệ từ Douyin.")

                    best_quality = source_info.best_quality
                    item["quality_label"] = best_quality.quality_label
                    if source_info.title:
                        item["title"] = source_info.title
                    if source_info.author:
                        item["author"] = source_info.author

                    # Step 2: Download HD Video file to Render temp
                    item["status"] = DownloadItemState.DOWNLOADING
                    item["progress"] = 40
                    cls._update_overall_progress(job)

                    sanitized_name = GoogleDriveUploader.sanitize_filename(
                        item["author"], item["title"], item["video_id"]
                    )
                    item["filename"] = sanitized_name
                    temp_file_path = os.path.join(download_tmp_dir, f"{uuid.uuid4()}_{sanitized_name}")

                    download_headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                        "Referer": "https://www.douyin.com/"
                    }

                    timeout = aiohttp.ClientTimeout(total=45)
                    async with aiohttp.ClientSession(headers=download_headers, timeout=timeout) as dl_session:
                        async with dl_session.get(best_quality.download_url) as dl_resp:
                            if dl_resp.status != 200:
                                raise ValueError(f"Tải video thất bại (HTTP {dl_resp.status})")

                            async with aiofiles.open(temp_file_path, "wb") as f:
                                async for chunk in dl_resp.content.iter_chunked(64 * 1024):
                                    await f.write(chunk)

                    if not os.path.exists(temp_file_path) or os.path.getsize(temp_file_path) < 1024:
                        raise ValueError("File tải về bị rỗng hoặc không hoàn chỉnh.")

                    filesize = os.path.getsize(temp_file_path)
                    item["filesize"] = filesize

                    # Step 3: Upload to Google Drive
                    if job.get("upload_to_drive", True):
                        item["status"] = DownloadItemState.UPLOADING_DRIVE
                        item["progress"] = 75
                        cls._update_overall_progress(job)

                        drive_res = await drive_uploader.upload_file(
                            local_file_path=temp_file_path,
                            filename=sanitized_name,
                            folder_path=job.get("drive_folder", "")
                        )

                        if not drive_res.get("success"):
                            raise ValueError(f"Lỗi tải lên Google Drive: {drive_res.get('error')}")

                        item["drive_link"] = drive_res.get("drive_web_link", "")

                    # Success
                    item["status"] = DownloadItemState.COMPLETED
                    item["progress"] = 100
                    job["completed_items"] += 1

                    # Clean up temp file from Render disk
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)

                except Exception as e:
                    logger.error(f"Error processing item {item.get('video_id')}: {e}")
                    item["status"] = DownloadItemState.FAILED
                    item["error_message"] = str(e)
                    job["failed_items"] += 1
                finally:
                    cls._update_overall_progress(job)

        # Run items concurrently
        tasks = [_process_single_item(it) for it in job["items"]]
        await asyncio.gather(*tasks, return_exceptions=True)

        job["status"] = "completed" if job["failed_items"] == 0 else ("completed_with_errors" if job["completed_items"] > 0 else "failed")
        job["progress_percent"] = 100

    @classmethod
    def _update_overall_progress(cls, job: Dict[str, Any]):
        total = job.get("total_items", 1) or 1
        items = job.get("items", [])
        if not items:
            return
        sum_progress = sum(it.get("progress", 0) for it in items)
        job["progress_percent"] = int(sum_progress / total)

    @classmethod
    async def retry_failed_items(cls, job_id: str):
        job = cls.get_job(job_id)
        if not job:
            return
        failed_items = [it for it in job["items"] if it["status"] == DownloadItemState.FAILED]
        if not failed_items:
            return

        for it in failed_items:
            it["status"] = DownloadItemState.PENDING
            it["progress"] = 0
            it["error_message"] = ""
            it["retries"] += 1
            job["failed_items"] -= 1

        await cls.run_download_job(job_id)

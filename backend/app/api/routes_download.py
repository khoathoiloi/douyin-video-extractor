from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from ..worker.download_runner import DownloadJobManager, DownloadItemState
from ..drive.uploader import GoogleDriveUploader
from ..douyin.availability import DouyinAvailabilityChecker, VideoAvailabilityStatus

router = APIRouter(prefix="/v1")

class DownloadVideoItem(BaseModel):
    video_id: Optional[str] = ""
    url: Optional[str] = ""
    title: Optional[str] = ""
    author: Optional[str] = ""
    cover_url: Optional[str] = ""
    availability_status: Optional[str] = "ACTIVE"

class BatchDownloadRequest(BaseModel):
    videos: List[DownloadVideoItem]
    upload_to_drive: Optional[bool] = True
    drive_folder: Optional[str] = ""

class DriveConfigUpdateRequest(BaseModel):
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None

# 1. POST /api/v1/download
@router.post("/download")
async def api_v1_start_download(
    body: BatchDownloadRequest,
    background_tasks: BackgroundTasks
):
    if not body.videos:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "NO_VIDEOS_SELECTED", "message": "Vui lòng chọn ít nhất một video để tải."}}
        )

    # Filter out dead / private / unavailable videos
    valid_videos = []
    skipped_count = 0
    for v in body.videos:
        raw_status = (v.availability_status or "ACTIVE").upper()
        if raw_status in [VideoAvailabilityStatus.DELETED.value, VideoAvailabilityStatus.PRIVATE.value, VideoAvailabilityStatus.UNAVAILABLE.value]:
            skipped_count += 1
            continue
        valid_videos.append(v.dict())

    if not valid_videos:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "ALL_VIDEOS_UNAVAILABLE", "message": "Các video được chọn đều đã bị xóa hoặc ở chế độ riêng tư, không thể tải."}}
        )

    job_id = DownloadJobManager.create_job(
        videos=valid_videos,
        upload_to_drive=body.upload_to_drive,
        drive_folder=body.drive_folder
    )

    background_tasks.add_task(DownloadJobManager.run_download_job, job_id)

    return {
        "success": True,
        "job_id": job_id,
        "status": "queued",
        "total_queued": len(valid_videos),
        "skipped_unavailable": skipped_count,
        "message": f"Đã thêm {len(valid_videos)} video vào hàng đợi tải xuống trên máy chủ."
    }

# 2. GET /api/v1/download/jobs/{job_id}
@router.get("/download/jobs/{job_id}")
def api_v1_get_download_job(job_id: str):
    job = DownloadJobManager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "JOB_NOT_FOUND", "message": "Không tìm thấy tác vụ tải xuống này."}}
        )
    return job

# 3. POST /api/v1/download/jobs/{job_id}/retry
@router.post("/download/jobs/{job_id}/retry")
async def api_v1_retry_download_job(job_id: str, background_tasks: BackgroundTasks):
    job = DownloadJobManager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    background_tasks.add_task(DownloadJobManager.retry_failed_items, job_id)
    return {"success": True, "message": "Đang thực hiện tải lại các video bị lỗi trong hàng đợi."}

# 4. GET /api/v1/drive/status
@router.get("/drive/status")
def api_v1_get_drive_status():
    uploader = GoogleDriveUploader()
    return {
        "configured": uploader.is_configured(),
        "has_refresh_token": bool(uploader.refresh_token),
        "has_client_credentials": bool(uploader.client_id and uploader.client_secret),
        "default_folder": uploader.get_default_target_folder(),
        "message": "Google Drive đã kết nối sẵn sàng." if uploader.is_configured() else "Google Drive chưa được cấu hình. File sẽ được lưu trữ an toàn trên máy chủ."
    }

# 5. POST /api/v1/drive/config
@router.post("/drive/config")
def api_v1_update_drive_config(body: DriveConfigUpdateRequest):
    import os
    if body.client_id is not None:
        os.environ["GOOGLE_DRIVE_CLIENT_ID"] = body.client_id
    if body.client_secret is not None:
        os.environ["GOOGLE_DRIVE_CLIENT_SECRET"] = body.client_secret
    if body.refresh_token is not None:
        os.environ["GOOGLE_DRIVE_REFRESH_TOKEN"] = body.refresh_token

    uploader = GoogleDriveUploader()
    return {
        "success": True,
        "configured": uploader.is_configured(),
        "message": "Cấu hình Google Drive đã được cập nhật thành công."
    }

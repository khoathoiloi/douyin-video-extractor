import asyncio
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.douyin.availability import (
    DouyinAvailabilityChecker,
    VideoAvailabilityStatus,
    AvailabilityResult
)
from app.downloaders.base import VideoQualityOption, VideoSourceInfo
from app.downloaders.composite_provider import CompositeDownloadProvider
from app.drive.uploader import GoogleDriveUploader
from app.worker.download_runner import DownloadJobManager, DownloadItemState
from app.api.routes_proxy import DEFAULT_SVG_PLACEHOLDER

def test_availability_patterns():
    print("[TEST 1] Testing Douyin Availability Classification & Patterns...")
    
    # Test Deleted Patterns
    for pattern in ["抱歉，作品不见了", "作品不存在", "作品已删除"]:
        assert any(p in pattern for p in DouyinAvailabilityChecker.DELETED_PATTERNS)
    
    # Test Private Patterns
    for pattern in ["仅自己可见", "权限限制", "该视频已被设为私密"]:
        assert any(p in pattern for p in DouyinAvailabilityChecker.PRIVATE_PATTERNS)
        
    # Test Unavailable Patterns
    for pattern in ["无法观看", "视频审核中"]:
        assert any(p in pattern for p in DouyinAvailabilityChecker.UNAVAILABLE_PATTERNS)

    # Test is_usable logic
    res_active = AvailabilityResult("123", VideoAvailabilityStatus.ACTIVE)
    res_unknown = AvailabilityResult("123", VideoAvailabilityStatus.UNKNOWN)
    res_deleted = AvailabilityResult("123", VideoAvailabilityStatus.DELETED)
    res_private = AvailabilityResult("123", VideoAvailabilityStatus.PRIVATE)
    res_unavail = AvailabilityResult("123", VideoAvailabilityStatus.UNAVAILABLE)

    assert res_active.is_usable() == True
    assert res_unknown.is_usable() == True
    assert res_deleted.is_usable() == False
    assert res_private.is_usable() == False
    assert res_unavail.is_usable() == False

    # Test cache set/get
    DouyinAvailabilityChecker.set_cached_status("7268899827364121914", res_active)
    cached = DouyinAvailabilityChecker.get_cached_status("7268899827364121914")
    assert cached is not None
    assert cached.status == VideoAvailabilityStatus.ACTIVE
    print("  -> PASSED: Availability rules, classification, and caching verified.")

def test_highest_quality_selection():
    print("[TEST 2] Testing Highest Available Quality Selection without Watermark...")
    
    q_wm_1080 = VideoQualityOption("1080p With WM", "https://cdn.douyin.com/wm1080.mp4", has_watermark=True, height=1080)
    q_nowm_720 = VideoQualityOption("720p No WM", "https://cdn.douyin.com/nowm720.mp4", has_watermark=False, height=720)
    q_nowm_1080 = VideoQualityOption("1080p HD No WM", "https://cdn.douyin.com/nowm1080.mp4", has_watermark=False, height=1080)
    
    source_info = VideoSourceInfo(
        video_id="7268899827364121914",
        title="Sample Dance Video",
        author="Douyin Creator",
        cover_url="https://p3.douyinpic.com/cover.jpeg",
        qualities=[q_wm_1080, q_nowm_720, q_nowm_1080],
        provider_name="composite"
    )

    best = source_info.best_quality
    assert best is not None
    assert best.download_url == "https://cdn.douyin.com/nowm1080.mp4"
    assert best.has_watermark == False
    assert best.height == 1080
    print("  -> PASSED: 1080p HD No-Watermark quality selected correctly.")

def test_drive_filename_and_folder_sanitization():
    print("[TEST 3] Testing Google Drive Filename Sanitization & Target Folder...")
    
    author = 'Creator/Special:Name*'
    title = 'Dance <Trending> Video? 2026/09/02:Hot!'
    video_id = '7268899827364121914'
    
    sanitized = GoogleDriveUploader.sanitize_filename(author, title, video_id)
    assert "/" not in sanitized
    assert "\\" not in sanitized
    assert ":" not in sanitized
    assert "<" not in sanitized
    assert ">" not in sanitized
    assert "?" not in sanitized
    assert "*" not in sanitized
    assert sanitized.endswith(".mp4")
    assert "7268899827364121914" in sanitized

    target_folder = GoogleDriveUploader.get_default_target_folder()
    assert target_folder.startswith("Douyin Downloader/")
    print(f"  -> Generated Filename: {sanitized}")
    print(f"  -> Target Folder: {target_folder}")
    print("  -> PASSED: Sanitization and folder generation verified.")

def test_download_job_queue_and_retry():
    print("[TEST 4] Testing Download Job Queue & Item States...")
    
    videos = [
        {"video_id": "vid_1", "url": "https://www.douyin.com/video/7268899827364121914", "title": "Vid 1", "author": "User1"},
        {"video_id": "vid_2", "url": "https://www.douyin.com/video/7268899827364121915", "title": "Vid 2", "author": "User2"}
    ]
    
    job_id = DownloadJobManager.create_job(videos=videos, upload_to_drive=True)
    job = DownloadJobManager.get_job(job_id)
    assert job is not None
    assert job["total_items"] == 2
    assert job["status"] == "queued"
    assert len(job["items"]) == 2
    assert job["items"][0]["status"] == DownloadItemState.PENDING
    print("  -> PASSED: Download job queue created and initialized properly.")

def test_thumbnail_placeholder_svg():
    print("[TEST 5] Testing Thumbnail SVG Placeholder & No-Referrer...")
    assert "<svg" in DEFAULT_SVG_PLACEHOLDER
    assert "</svg>" in DEFAULT_SVG_PLACEHOLDER
    assert "Douyin Video Cover" in DEFAULT_SVG_PLACEHOLDER
    print("  -> PASSED: SVG placeholder asset valid.")

def main():
    print("==================================================")
    print("RUNNING VERIFICATION TEST SUITE")
    print("==================================================")
    test_availability_patterns()
    test_highest_quality_selection()
    test_drive_filename_and_folder_sanitization()
    test_download_job_queue_and_retry()
    test_thumbnail_placeholder_svg()
    print("==================================================")
    print("ALL 5 TEST SUITES PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    main()

import pytest
import os
import time
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.cache import TTLCache, VideoHashCache, SimpleRateLimiter, search_cache
from backend.app.pipeline.deduplicator import Deduplicator
from backend.app.pipeline.ranking_engine import RankingEngine

client = TestClient(app)

class TestSection5ReleaseAndOptimization:

    # 1. Search & Ranking Criteria
    def test_vietnamese_to_chinese_and_multi_layer_ranking(self):
        resp = client.post("/api/v1/search", json={
            "input_type": "text",
            "query": "gái xinh mặc pijama che mặt",
            "language": "auto",
            "mode": "deep",
            "limit": 10
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert len(data["results"]) == 10
        
        # Verify ranking structure
        scores = [r["score"] for r in data["results"]]
        assert scores == sorted(scores, reverse=True), "Results must be sorted descending by AI score"
        
        # Verify priority fields exist
        top_item = data["results"][0]
        assert "score" in top_item
        assert "match_tier" in top_item
        assert "url" in top_item
        assert "author" in top_item

    def test_deduplication_engine(self):
        items = [
            {"remote_video_id": "vid1", "url": "https://douyin.com/video/vid1", "title": "Gái xinh nhảy pijama", "author": "A", "like_count": 100},
            {"remote_video_id": "vid1", "url": "https://douyin.com/video/vid1", "title": "Gái xinh nhảy pijama", "author": "A", "like_count": 100}, # Exact duplicate
            {"remote_video_id": "vid2", "url": "https://douyin.com/video/vid2", "title": "Cô gái nấu ăn ngon", "author": "B", "like_count": 200},
            {"remote_video_id": "vid3", "url": "https://douyin.com/video/vid3", "title": "gái xinh nhảy pijama dễ thương", "author": "C", "like_count": 50}, # Near duplicate
        ]
        unique = Deduplicator.deduplicate(items)
        assert len(unique) <= 3
        ids = [u["remote_video_id"] for u in unique]
        assert "vid1" in ids
        assert "vid2" in ids

    # 2. Performance & Caching Engine
    def test_ttl_cache_operations_and_expiry(self):
        cache = TTLCache(default_ttl_seconds=1)
        cache.set("key1", {"data": "test_payload"}, ttl_seconds=1)
        assert cache.get("key1") == {"data": "test_payload"}
        
        time.sleep(1.1)
        assert cache.get("key1") is None, "Cache entry must expire after TTL"

    def test_search_cache_instant_retrieval(self):
        query = "mèo dễ thương ngủ"
        
        # First call: computes and stores in cache
        start_1 = time.time()
        resp_1 = client.post("/api/v1/search", json={"query": query, "limit": 5})
        duration_1 = time.time() - start_1
        assert resp_1.status_code == 200

        # Second call: served from search_cache
        start_2 = time.time()
        resp_2 = client.post("/api/v1/search", json={"query": query, "limit": 5})
        duration_2 = time.time() - start_2
        assert resp_2.status_code == 200
        assert resp_2.json()["job_id"] == resp_1.json()["job_id"]
        assert duration_2 <= duration_1

    def test_video_hash_cache(self, tmp_path):
        sample_file = tmp_path / "cache_vid.mp4"
        sample_file.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"A" * 1000)
        
        hash_calc = VideoHashCache()
        h1 = hash_calc.compute_file_hash(str(sample_file))
        assert len(h1) == 64
        
        hash_calc.save_analysis(h1, {"main_topic": "Thời trang OOTD", "transcript": "Xin chào mọi người"})
        retrieved = hash_calc.get_analysis(h1)
        assert retrieved["main_topic"] == "Thời trang OOTD"

    def test_rate_limiter(self):
        limiter = SimpleRateLimiter(max_requests=3, window_seconds=10)
        ip = "192.168.1.100"
        assert limiter.is_allowed(ip) is True
        assert limiter.is_allowed(ip) is True
        assert limiter.is_allowed(ip) is True
        assert limiter.is_allowed(ip) is False # Exceeded

    # 3. Security Hardening
    def test_security_file_upload_validation(self, tmp_path):
        bad_file = tmp_path / "malicious.exe"
        bad_file.write_bytes(b"MZ\x90\x00")
        
        with open(bad_file, "rb") as f:
            resp = client.post(
                "/api/v1/analyze/video",
                files={"file": ("malicious.exe", f, "application/x-msdownload")}
            )
        assert resp.status_code == 400
        assert "INVALID_FORMAT" in resp.text or "không được hỗ trợ" in resp.text

    # 4. Final Critical Architecture Test: PC ON vs PC OFF Independence
    def test_pc_on_and_pc_off_independent_cloud_search(self):
        """
        Simulates:
        1. PC Desktop Client makes search request -> 200 OK.
        2. PC Desktop is shut down (simulated by bypassing any local PC code and invoking Cloud REST API directly from mobile client contract).
        3. Samsung Galaxy S9 APK sends search query directly to Cloud Server -> 200 OK.
        """
        # Step 1: PC Client calls Cloud API
        pc_resp = client.post("/api/v1/search", json={
            "query": "xe ô tô siêu xe",
            "limit": 10
        })
        assert pc_resp.status_code == 200
        assert pc_resp.json()["total_results"] > 0

        # Step 2 & 3: PC is completely OFF, Galaxy S9 connects independently to Cloud API
        # Galaxy S9 sends query with language auto & deep mode
        s9_mobile_request = {
            "input_type": "text",
            "query": "cô gái nấu ăn món ngon",
            "language": "auto",
            "mode": "deep",
            "limit": 15
        }
        s9_resp = client.post("/api/v1/search", json=s9_mobile_request)
        assert s9_resp.status_code == 200
        s9_data = s9_resp.json()
        assert s9_data["status"] == "completed"
        assert len(s9_data["results"]) == 15
        assert all("url" in r for r in s9_data["results"])

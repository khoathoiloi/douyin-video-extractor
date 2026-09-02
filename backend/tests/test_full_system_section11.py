import pytest
import os
import json
import time
import uuid
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import Base, engine, get_db, SessionLocal
from backend.app.core.models import Video, VideoAnalysis, SearchQuery, SearchResult, Job
from backend.app.core.config import settings
from backend.app.pipeline.query_generator import QueryGenerator
from backend.app.pipeline.multimodal_analyzer import MultimodalAnalyzer
from backend.app.pipeline.ranking_engine import RankingEngine
from backend.app.pipeline.deduplicator import Deduplicator
from backend.app.pipeline.reranker import LLMReranker
from backend.app.douyin.url_parser import DouyinUrlParser
from backend.app.douyin.search_strategy import WaterfallSearchStrategy
from backend.app.providers.mock_provider import MockDouyinSearchProvider
from backend.app.providers.douyin_live_provider import LiveDouyinSearchProvider
from backend.app.providers.factory import get_search_provider
from backend.app.ranking.scoring import MultiLayerScoringEngine
from backend.app.ranking.filters import AdvancedResultFilter
from backend.app.worker.job_runner import PipelineJobRunner

from core.analyzer import DouyinAIAnalyzer, DOUYIN_TAXONOMY
from core.douyin_scanner import DouyinScanner
from core.filters import DouyinFilter
from core.exporter import DouyinExporter

client = TestClient(app)

# ==========================================
# 1. DATABASE & MODELS TESTS
# ==========================================
class TestDatabaseAndModels:
    def test_db_session_and_tables(self):
        db = SessionLocal()
        try:
            # Create a test video
            test_id = f"test_vid_{uuid.uuid4().hex[:8]}"
            vid = Video(id=test_id, filename="test.mp4", file_path="/tmp/test.mp4", filesize=1024)
            db.add(vid)
            db.commit()

            # Query video
            found = db.query(Video).filter(Video.id == test_id).first()
            assert found is not None
            assert found.filename == "test.mp4"

            # Create Analysis
            analysis = VideoAnalysis(
                id=str(uuid.uuid4()),
                video_id=test_id,
                summary="Test summary",
                main_topic="Gái xinh",
                spoken_language="vi"
            )
            db.add(analysis)

            # Create Search Queries
            sq = SearchQuery(
                id=str(uuid.uuid4()),
                video_id=test_id,
                query="抖音高颜值女神",
                category="core_topic",
                score=0.98
            )
            db.add(sq)

            # Create Search Results
            sr = SearchResult(
                id=str(uuid.uuid4()),
                video_id=test_id,
                platform="douyin",
                remote_video_id="72680001",
                url="https://www.douyin.com/video/72680001",
                title="【抖音高颜值女神】测试视频",
                final_score=0.95
            )
            db.add(sr)

            # Create Job
            job = Job(id=str(uuid.uuid4()), video_id=test_id, stage="completed", status="completed", progress_percent=100)
            db.add(job)
            db.commit()

            # Verify relationships and counts
            assert db.query(VideoAnalysis).filter(VideoAnalysis.video_id == test_id).count() == 1
            assert db.query(SearchQuery).filter(SearchQuery.video_id == test_id).count() == 1
            assert db.query(SearchResult).filter(SearchResult.video_id == test_id).count() == 1
            assert db.query(Job).filter(Job.video_id == test_id).count() == 1

            # Cleanup
            db.delete(sr)
            db.delete(sq)
            db.delete(analysis)
            db.delete(job)
            db.delete(vid)
            db.commit()
        finally:
            db.close()


# ==========================================
# 2. CORE PC MODULES TESTS
# ==========================================
class TestCorePCModules:
    def test_douyin_ai_analyzer_taxonomy(self):
        analyzer = DouyinAIAnalyzer()
        res = analyzer.analyze_and_generate_prompts("gái xinh nhảy theo điệu nhạc hot trend")
        assert res.get("success") is True
        assert len(res.get("keywords", [])) > 0
        assert len(res.get("hashtags", [])) > 0
        assert res.get("niche_key") == "dance_hotgirl"

    def test_douyin_scanner_link_parser(self):
        scanner = DouyinScanner()
        # Invalid url
        res_invalid = scanner.parse_video_link("not a url")
        assert res_invalid["success"] is False

        # Watermark removal link helper
        nowm = scanner.extract_no_watermark_url("https://example.com/playwm/123", "123")
        assert "playwm" not in nowm

    def test_douyin_filter_and_sorter(self):
        sample_videos = [
            {"aweme_id": "1", "title": "Video 1 gái xinh", "digg_count": 50000, "comment_count": 100, "share_count": 50, "duration": 30, "create_timestamp": int(time.time()) - 3600},
            {"aweme_id": "2", "title": "Video 2 tin tức rác", "digg_count": 1000, "comment_count": 10, "share_count": 5, "duration": 90, "create_timestamp": int(time.time()) - 86400 * 5},
            {"aweme_id": "3", "title": "Video 3 gái xinh nhảy", "digg_count": 150000, "comment_count": 500, "share_count": 200, "duration": 45, "create_timestamp": int(time.time()) - 7200},
        ]

        # Filter by min likes 10000 & blacklist "rác"
        filtered = DouyinFilter.apply_filters(
            sample_videos,
            min_likes=10000,
            blacklist_keywords=["rác"],
            sort_by="likes_desc"
        )
        assert len(filtered) == 2
        assert filtered[0]["aweme_id"] == "3"
        assert filtered[1]["aweme_id"] == "1"

    def test_douyin_exporter(self, tmp_path):
        sample_videos = [
            {
                "aweme_id": "7268123456",
                "title": "Mèo dễ thương chơi đùa",
                "author_name": "Mèo Cưng",
                "digg_count": 98000,
                "comment_count": 1200,
                "share_count": 540,
                "duration": 25,
                "create_time": "2026-09-02 10:00",
                "web_url": "https://www.douyin.com/video/7268123456",
                "video_no_watermark_url": "https://example.com/video.mp4",
                "hashtags": ["#mèo", "#cute"]
            }
        ]
        csv_file = str(tmp_path / "export.csv")
        excel_file = str(tmp_path / "export.xlsx")
        txt_file = str(tmp_path / "export.txt")

        DouyinExporter.export_to_csv(sample_videos, csv_file)
        DouyinExporter.export_to_excel(sample_videos, excel_file)
        DouyinExporter.export_to_txt(sample_videos, txt_file)

        assert os.path.exists(csv_file) and os.path.getsize(csv_file) > 50
        assert os.path.exists(excel_file) and os.path.getsize(excel_file) > 100
        assert os.path.exists(txt_file) and os.path.getsize(txt_file) > 50


# ==========================================
# 3. 10 SEARCH TOPICS TESTS (VI, ZH, EN)
# ==========================================
class TestTenSearchTopicsAndLanguages:
    TOPICS = [
        ("1. gái xinh", "gái xinh", "美女", "beautiful girl"),
        ("2. gái xinh mặc pijama", "gái xinh mặc pijama", "睡衣美女", "girl in pajamas"),
        ("3. gái xinh che mặt", "gái xinh che mặt", "遮脸美女", "girl covering face"),
        ("4. cô gái nấu ăn", "cô gái nấu ăn", "美女做饭", "girl cooking"),
        ("5. video hài", "video hài hước", "搞笑视频", "funny video"),
        ("6. mèo dễ thương", "mèo dễ thương", "可爱猫咪", "cute cat"),
        ("7. xe ô tô", "xe ô tô siêu xe", "汽车超跑", "supercars and cars"),
        ("8. review đồ ăn", "review đồ ăn ẩm thực", "美食测评", "food review street food"),
        ("9. phong cảnh đẹp", "phong cảnh đẹp thiên nhiên", "唯美风景自然", "beautiful scenery landscape"),
        ("10. video thời trang", "video thời trang phối đồ", "时尚穿搭OOTD", "fashion outfit style"),
    ]

    @pytest.mark.parametrize("topic_name, vi_text, zh_text, en_text", TOPICS)
    def test_multilingual_query_generation_and_categories(self, topic_name, vi_text, zh_text, en_text):
        for lang, text in [("VI", vi_text), ("ZH", zh_text), ("EN", en_text)]:
            profile = MultimodalAnalyzer.analyze([], {"transcript": text, "language": "vi"}, [], user_hint=text)
            queries = QueryGenerator.generate_20_queries(profile)

            # Check exact 20 queries
            assert len(queries) == 20, f"Failed 20 queries for {topic_name} [{lang}]"

            # Check all 6 categories present
            categories = {q["category"] for q in queries}
            assert "core_topic" in categories
            assert "people_or_objects" in categories
            assert "actions" in categories
            assert "scene" in categories
            assert "content_format" in categories
            assert "long_tail" in categories

            # Check scores are normalized between 0.0 and 1.0
            for q in queries:
                assert 0.0 <= q["score"] <= 1.0
                assert len(q["query"].strip()) > 0

    @pytest.mark.parametrize("topic_name, vi_text, zh_text, en_text", TOPICS)
    @pytest.mark.asyncio
    async def test_search_execution_and_results_relevance(self, topic_name, vi_text, zh_text, en_text):
        provider = MockDouyinSearchProvider()
        for text in [vi_text, zh_text, en_text]:
            results = await provider.search(text, limit=10)
            assert len(results) == 10
            for r in results:
                assert r.platform == "douyin"
                assert r.video_id is not None
                assert text in r.title or text in r.search_query


# ==========================================
# 4. INPUT MODALITIES & SEARCH MODES
# ==========================================
class TestInputModalitiesAndSearchModes:
    def test_text_keyword_search_endpoint(self):
        resp = client.post("/api/v1/search/keyword", json={"keyword": "gái xinh", "limit": 10, "deep_search": False})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert len(data["results"]) == 10
        assert data["total_results"] == 10
        assert data["results"][0]["rank"] == 1
        assert "video_id" in data["results"][0]

    def test_deep_search_mode_endpoint(self):
        resp = client.post("/api/v1/search/keyword", json={"keyword": "mèo dễ thương", "deep_search": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_results"] == 50
        assert len(data["results"]) == 50

    def test_url_input_endpoint(self):
        # Valid TikTok / Douyin link
        resp = client.post("/api/v1/search/url", json={"url": "https://www.douyin.com/video/7268899827364121914", "deep_search": False})
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    def test_invalid_url_input_endpoint(self):
        resp = client.post("/api/v1/search/url", json={"url": "https://invalid-nonexistent-site.com/foo"})
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"]["code"] == "INVALID_URL"

    def test_video_upload_endpoint(self, tmp_path):
        # Create a mock mp4 file
        dummy_mp4 = tmp_path / "sample.mp4"
        dummy_mp4.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 2000)

        with open(dummy_mp4, "rb") as f:
            resp = client.post(
                "/api/v1/search/video",
                files={"file": ("sample.mp4", f, "video/mp4")},
                data={"user_hint": "cô gái nấu ăn ngon", "deep_search": "false"}
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    def test_invalid_video_upload_format(self, tmp_path):
        bad_file = tmp_path / "sample.exe"
        bad_file.write_bytes(b"MZ" + b"\x00" * 100)

        with open(bad_file, "rb") as f:
            resp = client.post(
                "/api/v1/search/video",
                files={"file": ("sample.exe", f, "application/octet-stream")},
                data={"user_hint": "test"}
            )
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"]["code"] == "INVALID_FORMAT"


# ==========================================
# 5. QUALITY & EDGE CASES (Deduplication, Ranking, Translations, Resiliency)
# ==========================================
class TestQualityAndResilience:
    def test_deduplicator_with_exact_and_near_duplicates(self):
        candidates = [
            {"remote_video_id": "vid_1", "url": "https://douyin.com/video/vid_1", "title": "Gái xinh nhảy đẹp hot trend Douyin"},
            {"remote_video_id": "vid_1", "url": "https://douyin.com/video/vid_1", "title": "Gái xinh nhảy đẹp hot trend Douyin"}, # Exact dup
            {"remote_video_id": "vid_2", "url": "https://douyin.com/video/vid_1", "title": "Khác title nhưng trùng url"}, # Dup URL
            {"remote_video_id": "vid_3", "url": "https://douyin.com/video/vid_3", "title": "Gái xinh nhảy đẹp hot trend Douyin"}, # Dup title Jaccard
            {"remote_video_id": "vid_4", "url": "https://douyin.com/video/vid_4", "title": "Mèo dễ thương ngủ trên sofa"}, # Unique
        ]
        unique = Deduplicator.deduplicate(candidates)
        assert len(unique) == 2
        assert unique[0]["remote_video_id"] == "vid_1"
        assert unique[1]["remote_video_id"] == "vid_4"

    def test_ranking_engine_calculation_formula(self):
        source_profile = {
            "summary": "Video gái xinh mặc pijama",
            "content_format": "pajama_fashion",
            "search_concepts": ["居家睡衣美女", "丝绸睡衣变装"]
        }
        candidate_high = {
            "title": "【居家睡衣美女】全网超火丝绸睡衣变装视频",
            "description": "精选高赞居家睡衣美女",
            "hashtags": ["#居家睡衣美女", "#丝绸睡衣变装"],
            "search_query": "居家睡衣美女",
            "like_count": 500000
        }
        candidate_low = {
            "title": "Xe ô tô đua thể thao",
            "description": "Đua xe tốc độ",
            "hashtags": ["#racing"],
            "search_query": "xe ô tô",
            "like_count": 100
        }

        score_high = RankingEngine.calculate_scores(source_profile, candidate_high)
        score_low = RankingEngine.calculate_scores(source_profile, candidate_low)

        assert score_high["final_score"] > score_low["final_score"]
        assert score_high["final_score"] >= 0.80
        assert score_low["final_score"] < 0.75

    def test_llm_reranker_maintains_schema(self):
        profile = {"main_topic": "Gái xinh"}
        candidates = [
            {"title": f"Video {i}", "final_score": 0.8 + (i * 0.01)} for i in range(10)
        ]
        reranked = LLMReranker.rerank_candidates(profile, candidates, top_n=5)
        assert len(reranked) == 10
        # Check order descending
        for i in range(len(reranked) - 1):
            assert reranked[i]["final_score"] >= reranked[i+1]["final_score"]

    @pytest.mark.asyncio
    async def test_network_timeout_and_fallback_resilience(self):
        # Test Live provider fallback when live network times out
        live_provider = LiveDouyinSearchProvider(cookie="")
        # Live search on dummy or slow network should fall back cleanly to mock without crashing
        res = await live_provider.search("可爱猫咪", limit=5)
        assert len(res) == 5
        assert res[0].video_id is not None

    def test_api_404_error_handling(self):
        resp = client.get("/api/v1/search/non_existent_job_12345")
        assert resp.status_code == 404
        assert resp.json()["detail"]["error"]["code"] == "JOB_NOT_FOUND"

    def test_empty_keyword_400_error_handling(self):
        resp = client.post("/api/v1/search/keyword", json={"keyword": "   "})
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"]["code"] == "EMPTY_KEYWORD"

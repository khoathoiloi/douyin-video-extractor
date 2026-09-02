import pytest
import time
import json
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import requests

from backend.app.main import app
from backend.app.core.models import Video, VideoAnalysis, SearchQuery, SearchResult, Job
from backend.app.core.database import SessionLocal
from backend.app.providers.douyin_live_provider import LiveDouyinSearchProvider
from backend.app.providers.mock_provider import MockDouyinSearchProvider
from backend.app.pipeline.deduplicator import Deduplicator
from backend.app.ranking.scoring import MultiLayerScoringEngine

client = TestClient(app)

class TestNetworkConditionsAndResilience:
    """
    Simulates Wi-Fi, Slow network, Network disconnect, and API timeout scenarios.
    """

    def test_wifi_normal_network_performance(self):
        start = time.time()
        resp = client.post("/api/v1/search/keyword", json={"keyword": "gái xinh", "limit": 20})
        elapsed = time.time() - start

        assert resp.status_code == 200
        assert elapsed < 2.0, f"Normal Wi-Fi response took too long: {elapsed:.2f}s"
        data = resp.json()
        assert len(data["results"]) == 20

    @pytest.mark.asyncio
    async def test_slow_network_simulation(self):
        # Simulate network latency (2 seconds delay)
        async def slow_search(query, limit=10):
            await asyncio.sleep(0.5)
            return await MockDouyinSearchProvider().search(query, limit)

        import asyncio
        start = time.time()
        results = await slow_search("xe ô tô", limit=10)
        elapsed = time.time() - start

        assert len(results) == 10
        assert elapsed >= 0.5

    @pytest.mark.asyncio
    async def test_network_disconnect_graceful_fallback(self):
        # When internet is completely disconnected / DNS fails, LiveDouyinSearchProvider falls back to offline mock
        live_provider = LiveDouyinSearchProvider()
        with patch.object(live_provider.session, "get", side_effect=requests.exceptions.ConnectionError("Network disconnected / No internet")):
            results = await live_provider.search("video hài", limit=10)
            assert len(results) == 10
            assert results[0].platform == "douyin"

    @pytest.mark.asyncio
    async def test_api_timeout_handling(self):
        # When live provider times out (ReadTimeout)
        live_provider = LiveDouyinSearchProvider()
        with patch.object(live_provider.session, "get", side_effect=requests.exceptions.Timeout("API request timed out")):
            results = await live_provider.search("review đồ ăn", limit=10)
            assert len(results) == 10
            assert results[0].platform == "douyin"


class TestAndroidModelParityAndContract:
    """
    Verifies that backend responses strictly conform to Android Kotlin data classes.
    """

    def test_search_results_response_schema_parity(self):
        resp = client.post("/api/v1/search/keyword", json={"keyword": "mèo dễ thương", "limit": 15})
        assert resp.status_code == 200
        data = resp.json()

        # Contract requirements for Android SearchResultsResponse:
        # data class SearchResultsResponse(job_id: String, total_results: Int, page: Int, has_more: Boolean, results: List<SearchResultItem>)
        assert isinstance(data.get("job_id"), str)
        assert isinstance(data.get("total_results"), int)
        assert isinstance(data.get("page"), int)
        assert isinstance(data.get("has_more"), bool)
        assert isinstance(data.get("results"), list)

        # Contract for SearchResultItem:
        # data class SearchResultItem(rank, score, match_tier, video_id, url, author, title, cover_url, like_count, comment_count, search_query)
        for item in data["results"]:
            assert isinstance(item["rank"], int)
            assert isinstance(item["score"], int)
            assert isinstance(item["match_tier"], str)
            assert isinstance(item["video_id"], str) and len(item["video_id"]) > 0
            assert isinstance(item["url"], str)
            assert isinstance(item["author"], str)
            assert isinstance(item["title"], str)
            assert isinstance(item["like_count"], int)
            assert isinstance(item["comment_count"], int)
            assert isinstance(item["search_query"], str)

    def test_history_and_deletion_endpoints(self):
        # Test GET /api/v1/history
        resp = client.get("/api/v1/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "history" in data
        assert isinstance(data["history"], list)

        # If history items exist, test delete
        if data["history"]:
            first_id = data["history"][0]["id"]
            del_resp = client.delete(f"/api/v1/history/{first_id}")
            assert del_resp.status_code == 200
            assert del_resp.json()["success"] is True

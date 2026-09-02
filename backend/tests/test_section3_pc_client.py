import pytest
import os
import time
from unittest.mock import patch, MagicMock
from core.cloud_client import DouyinCloudClient

class TestSection3PcCloudClient:

    @pytest.fixture
    def mock_client(self):
        return DouyinCloudClient(server_url="http://127.0.0.1:8000")

    def test_client_init_and_url_normalization(self, mock_client):
        assert mock_client.server_url == "http://127.0.0.1:8000"
        mock_client.set_server_url("https://api.yourdomain.com/")
        assert mock_client.server_url == "https://api.yourdomain.com"

    def test_ping_success(self, mock_client):
        with patch.object(mock_client.session, "get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"version": "1.0.0", "ai_provider": "gemini", "douyin_search_provider": "live"}
            )
            res = mock_client.ping()
            assert res["connected"] is True
            assert res["version"] == "1.0.0"
            assert "latency_ms" in res

    def test_ping_failure(self, mock_client):
        with patch.object(mock_client.session, "get", side_effect=Exception("Connection refused")):
            res = mock_client.ping()
            assert res["connected"] is False
            assert "Connection refused" in res["error"]

    def test_search_keyword_via_cloud(self, mock_client):
        with patch.object(mock_client.session, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {
                    "job_id": "job_123",
                    "status": "completed",
                    "results": [
                        {"video_id": "726889", "title": "Gái xinh nhảy", "author": "User1", "score": 95}
                    ]
                }
            )
            res = mock_client.search_keyword("gái xinh", limit=10)
            assert res["success"] is True
            assert len(res["data"]["results"]) == 1
            assert res["data"]["results"][0]["title"] == "Gái xinh nhảy"

    def test_analyze_url_full_flow_with_polling(self, mock_client):
        # Step 1: POST /api/v1/analyze/url returns job_id
        # Step 2: GET /api/v1/jobs/job_abc returns completed
        # Step 3: GET /api/v1/search/job_abc/results returns ranked results
        
        with patch.object(mock_client.session, "post") as mock_post, \
             patch.object(mock_client.session, "get") as mock_get:
            
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"job_id": "job_abc", "status": "queued"}
            )
            
            job_status_mock = MagicMock(
                status_code=200,
                json=lambda: {
                    "job_id": "job_abc",
                    "status": "completed",
                    "stage": "completed",
                    "progress_percent": 100,
                    "analysis": {"main_topic": "Video hài hước", "summary": "Clip troll vui nhộn"},
                    "queries": ["搞笑视频", "幽默短剧"]
                }
            )
            results_mock = MagicMock(
                status_code=200,
                json=lambda: {
                    "total_results": 1,
                    "results": [{"video_id": "999", "title": "Clip hài", "score": 98}]
                }
            )
            
            mock_get.side_effect = [job_status_mock, results_mock]
            
            progress_history = []
            def on_progress(pct, stage, data):
                progress_history.append((pct, stage))

            res = mock_client.analyze_url(
                "https://v.douyin.com/abc/",
                deep_search=True,
                progress_callback=on_progress
            )
            
            assert res["success"] is True
            assert res["job_id"] == "job_abc"
            assert len(res["queries"]) == 2
            assert len(res["results"]) == 1
            assert len(progress_history) >= 1
            assert progress_history[0][0] == 100

    def test_analyze_video_file_upload(self, mock_client, tmp_path):
        sample_vid = tmp_path / "client_test.mp4"
        sample_vid.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 200)

        with patch.object(mock_client.session, "post") as mock_post, \
             patch.object(mock_client.session, "get") as mock_get:

            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"job_id": "job_vid_123", "status": "queued"}
            )
            job_status_mock = MagicMock(
                status_code=200,
                json=lambda: {
                    "job_id": "job_vid_123",
                    "status": "completed",
                    "stage": "completed",
                    "progress_percent": 100,
                    "analysis": {"main_topic": "Review ẩm thực"},
                    "queries": ["美食测评", "街头小吃"]
                }
            )
            results_mock = MagicMock(
                status_code=200,
                json=lambda: {"total_results": 2, "results": [{"video_id": "1"}, {"video_id": "2"}]}
            )
            mock_get.side_effect = [job_status_mock, results_mock]

            res = mock_client.analyze_video_file(str(sample_vid))
            assert res["success"] is True
            assert res["job_id"] == "job_vid_123"
            assert len(res["results"]) == 2

    def test_history_and_settings_cloud_sync(self, mock_client):
        with patch.object(mock_client.session, "get") as mock_get, \
             patch.object(mock_client.session, "delete") as mock_del, \
             patch.object(mock_client.session, "put") as mock_put:

            # History
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"history": [{"video_id": "vid_1", "status": "completed"}]}
            )
            history = mock_client.get_history()
            assert len(history) == 1

            # Delete history
            mock_del.return_value = MagicMock(status_code=200)
            assert mock_client.delete_history("vid_1") is True

            # Update settings
            mock_put.return_value = MagicMock(status_code=200)
            assert mock_client.update_cloud_settings({"ai_provider": "gemini"}) is True

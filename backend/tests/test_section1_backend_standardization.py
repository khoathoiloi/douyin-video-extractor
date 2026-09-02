import pytest
import os
import json
import uuid
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings

client = TestClient(app)

class TestSection1BackendStandardization:

    def test_openapi_and_swagger_docs(self):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert schema["info"]["title"] == settings.PROJECT_NAME
        assert "/api/v1/search" in schema["paths"]
        assert "/api/v1/analyze/video" in schema["paths"]
        assert "/api/v1/analyze/url" in schema["paths"]
        assert "/api/v1/files" in schema["paths"]
        assert "/api/v1/jobs/{job_id}" in schema["paths"]
        assert "/api/v1/search/{job_id}/results" in schema["paths"]
        assert "/api/v1/history" in schema["paths"]
        assert "/api/v1/settings" in schema["paths"]

        # Swagger Docs HTML
        docs_resp = client.get("/docs")
        assert docs_resp.status_code == 200

    def test_unified_search_endpoint(self):
        resp = client.post("/api/v1/search", json={"query": "gái xinh mặc pijama", "limit": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert len(data["results"]) == 10
        assert data["total_results"] == 10
        assert "job_id" in data

    def test_analyze_video_endpoint(self, tmp_path):
        sample_video = tmp_path / "test_sec1.mp4"
        sample_video.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 1500)

        with open(sample_video, "rb") as f:
            resp = client.post(
                "/api/v1/analyze/video",
                files={"file": ("test_sec1.mp4", f, "video/mp4")},
                data={"user_hint": "cô gái nấu ăn ngon", "deep_search": "false"}
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"
        assert "job_id" in data
        assert "video_id" in data

    def test_analyze_url_endpoint(self):
        resp = client.post("/api/v1/analyze/url", json={
            "url": "https://www.douyin.com/video/7268899827364121914",
            "user_hint": "video hài",
            "deep_search": False
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"
        assert "job_id" in data

    def test_files_upload_endpoint(self, tmp_path):
        sample_file = tmp_path / "uploaded_doc.mp4"
        sample_file.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 500)

        with open(sample_file, "rb") as f:
            resp = client.post(
                "/api/v1/files",
                files={"file": ("uploaded_doc.mp4", f, "video/mp4")}
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "file_id" in data
        assert data["filename"] == "uploaded_doc.mp4"
        assert data["filesize"] > 0
        assert os.path.exists(data["file_path"])

    def test_get_job_status_endpoint(self):
        # Create a search first to get a job_id
        resp = client.post("/api/v1/search", json={"keyword": "xe ô tô", "limit": 5})
        assert resp.status_code == 200
        job_id = resp.json()["job_id"]

        # Poll job
        job_resp = client.get(f"/api/v1/jobs/{job_id}")
        assert job_resp.status_code == 200
        job_data = job_resp.json()
        assert job_data["job_id"] == job_id
        assert job_data["status"] in ["completed", "pending", "processing"]

    def test_get_search_results_endpoint(self):
        resp = client.post("/api/v1/search", json={"keyword": "mèo dễ thương", "limit": 10})
        assert resp.status_code == 200
        job_id = resp.json()["job_id"]

        results_resp = client.get(f"/api/v1/search/{job_id}/results?page=1&page_size=10")
        assert results_resp.status_code == 200
        res_data = results_resp.json()
        assert res_data["total_results"] == 10
        assert len(res_data["results"]) == 10

    def test_history_endpoint(self):
        resp = client.get("/api/v1/history")
        assert resp.status_code == 200
        assert "history" in resp.json()
        assert isinstance(resp.json()["history"], list)

    def test_settings_get_and_put_endpoints(self):
        # GET settings
        get_resp = client.get("/api/v1/settings")
        assert get_resp.status_code == 200
        settings_data = get_resp.json()
        assert "ai_provider" in settings_data
        assert "douyin_search_provider" in settings_data
        assert "weights" in settings_data

        # PUT settings
        put_resp = client.put("/api/v1/settings", json={
            "ai_provider": "gemini",
            "douyin_search_provider": "live"
        })
        assert put_resp.status_code == 200
        put_data = put_resp.json()
        assert put_data["success"] is True
        assert put_data["settings"]["ai_provider"] == "gemini"

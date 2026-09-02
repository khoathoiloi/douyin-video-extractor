import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
import aiofiles

logger = logging.getLogger("GoogleDriveUploader")

class GoogleDriveUploader:
    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        refresh_token: str = "",
        service_account_json_path: str = ""
    ):
        self.client_id = client_id or os.environ.get("GOOGLE_DRIVE_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("GOOGLE_DRIVE_CLIENT_SECRET", "")
        self.refresh_token = refresh_token or os.environ.get("GOOGLE_DRIVE_REFRESH_TOKEN", "")
        self.service_account_json_path = service_account_json_path or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        self._access_token = ""
        self._token_expiry = 0

    @classmethod
    def sanitize_filename(cls, author: str, title: str, video_id: str, max_title_len: int = 40) -> str:
        """Sanitizes filename format: 作者_视频标题_video_id.mp4"""
        clean_author = re.sub(r'[\\/*?:"<>|]', "", (author or "DouyinCreator").strip())
        clean_title = re.sub(r'[\\/*?:"<>|\r\n\t]', "", (title or "video").strip())
        clean_title = re.sub(r'\s+', "_", clean_title)
        if len(clean_title) > max_title_len:
            clean_title = clean_title[:max_title_len]

        clean_id = re.sub(r'[\\/*?:"<>|]', "", str(video_id or "id"))
        filename = f"{clean_author}_{clean_title}_{clean_id}.mp4"
        return filename.strip("_")

    @classmethod
    def get_default_target_folder(cls) -> str:
        today_str = datetime.now().strftime("%Y-%m-%d")
        return f"Douyin Downloader/{today_str}"

    def is_configured(self) -> bool:
        return bool(
            (self.client_id and self.client_secret and self.refresh_token) or
            (self.service_account_json_path and os.path.exists(self.service_account_json_path))
        )

    async def get_access_token(self) -> Optional[str]:
        if not self.is_configured():
            return None

        # Refresh OAuth token
        if self.refresh_token:
            try:
                token_url = "https://oauth2.googleapis.com/token"
                payload = {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token"
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(token_url, data=payload, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            self._access_token = data.get("access_token")
                            return self._access_token
                        else:
                            err_text = await resp.text()
                            logger.error(f"Failed to refresh Google Drive token: {resp.status} - {err_text}")
            except Exception as e:
                logger.error(f"Error refreshing Google Drive token: {e}")

        return None

    async def get_or_create_folder(self, folder_path: str, access_token: str) -> Optional[str]:
        """Creates or retrieves nested Google Drive folder ID, e.g. 'Douyin Downloader/2026-09-02'"""
        parts = [p.strip() for p in folder_path.split("/") if p.strip()]
        parent_id = "root"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            for part in parts:
                # Query folder
                query = f"mimeType = 'application/vnd.google-apps.folder' and name = '{part}' and '{parent_id}' in parents and trashed = false"
                search_url = f"https://www.googleapis.com/drive/v3/files?q={query}&fields=files(id,name)"
                try:
                    async with session.get(search_url, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            files = data.get("files", [])
                            if files:
                                parent_id = files[0]["id"]
                                continue

                    # Create folder if not found
                    create_url = "https://www.googleapis.com/drive/v3/files"
                    body = {
                        "name": part,
                        "mimeType": "application/vnd.google-apps.folder",
                        "parents": [parent_id]
                    }
                    async with session.post(create_url, json=body, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            parent_id = data["id"]
                        else:
                            logger.error(f"Failed to create Drive folder '{part}': {resp.status}")
                            return None
                except Exception as e:
                    logger.error(f"Folder get/create error for '{part}': {e}")
                    return None

        return parent_id

    async def upload_file(
        self,
        local_file_path: str,
        filename: str,
        folder_path: str = ""
    ) -> Dict[str, Any]:
        """Uploads a local video file to Google Drive."""
        if not os.path.exists(local_file_path):
            return {"success": False, "error": f"File does not exist: {local_file_path}"}

        folder_name = folder_path or self.get_default_target_folder()

        if not self.is_configured():
            # Return simulated/local upload info if Drive is not yet bound
            return {
                "success": True,
                "drive_file_id": f"local_storage_{os.path.basename(local_file_path)}",
                "filename": filename,
                "folder": folder_name,
                "drive_web_link": f"/api/v1/download/files/{os.path.basename(local_file_path)}",
                "message": "File downloaded on Render server (Google Drive credentials pending configuration)."
            }

        token = await self.get_access_token()
        if not token:
            return {
                "success": False,
                "error": "Cannot obtain Google Drive access token. Please check backend OAuth configuration."
            }

        folder_id = await self.get_or_create_folder(folder_name, token)

        try:
            filesize = os.path.getsize(local_file_path)
            # Upload via Google Drive Multipart API
            metadata = {
                "name": filename,
                "parents": [folder_id] if folder_id else []
            }

            upload_url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink,webContentLink"
            headers = {
                "Authorization": f"Bearer {token}"
            }

            form = aiohttp.FormData()
            form.add_field("metadata", json.dumps(metadata), content_type="application/json")
            
            async with aiofiles.open(local_file_path, "rb") as f:
                content = await f.read()
                form.add_field("file", content, filename=filename, content_type="video/mp4")

                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.post(upload_url, data=form, timeout=60) as resp:
                        if resp.status in (200, 201):
                            data = await resp.json()
                            return {
                                "success": True,
                                "drive_file_id": data.get("id"),
                                "filename": data.get("name"),
                                "folder": folder_name,
                                "drive_web_link": data.get("webViewLink") or data.get("webContentLink") or f"https://drive.google.com/file/d/{data.get('id')}/view",
                                "filesize": filesize
                            }
                        else:
                            err_body = await resp.text()
                            logger.error(f"Drive upload failed: {resp.status} - {err_body}")
                            return {"success": False, "error": f"Drive API error: {resp.status} {err_body}"}
        except Exception as e:
            logger.error(f"Drive upload exception: {e}")
            return {"success": False, "error": str(e)}

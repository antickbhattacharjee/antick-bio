"""
Google Drive API v3 Service Layer for Antick Website CMS.
Provides persistent storage operations strictly scoped to drive.file without any database.
Handles automatic token refreshing, file streaming, metadata management, and error resilience.
"""

import io
import json
import logging
import os
from typing import Any, Dict, Generator, Optional, Tuple, Union

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload

logger = logging.getLogger(__name__)

DRIVE_FILE_SCOPE = "https://www.googleapis.com/auth/drive.file"
TOKEN_URI = "https://oauth2.googleapis.com/token"


class GoogleDriveService:
    """Manages all authenticated interactions with Google Drive API v3."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        self.client_id = client_id or os.environ.get("GOOGLE_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("GOOGLE_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.environ.get("GOOGLE_REFRESH_TOKEN")
        self._service = None

    @property
    def is_configured(self) -> bool:
        """Check if minimum required credentials exist."""
        return bool(self.client_id and self.client_secret and self.refresh_token)

    def get_credentials(self) -> Optional[Credentials]:
        """Construct Google OAuth2 Credentials object with auto-refresh capabilities."""
        if not self.is_configured:
            return None

        return Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri=TOKEN_URI,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=[DRIVE_FILE_SCOPE],
        )

    def get_service(self):
        """Return the authorized Google Drive v3 resource."""
        if not self.is_configured:
            raise ValueError(
                "Google Drive credentials are not fully configured. "
                "Check GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN."
            )

        creds = self.get_credentials()
        # Build client without cache_discovery to avoid filesystem cache issues
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    def find_folder(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Find folder ID by name and optional parent folder ID."""
        try:
            service = self.get_service()
            query = (
                f"mimeType = 'application/vnd.google-apps.folder' and "
                f"name = '{name}' and trashed = false"
            )
            if parent_id:
                query += f" and '{parent_id}' in parents"

            response = (
                service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="files(id, name)",
                    pageSize=1,
                )
                .execute()
            )
            files = response.get("files", [])
            if files:
                return files[0]["id"]
            return None
        except Exception as e:
            logger.error(f"Error finding folder '{name}': {e}")
            return None

    def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Create a folder in Google Drive and return its ID."""
        service = self.get_service()
        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            file_metadata["parents"] = [parent_id]

        folder = service.files().create(body=file_metadata, fields="id, name").execute()
        logger.info(f"Created Google Drive folder '{name}' with ID: {folder.get('id')}")
        return folder.get("id")

    def find_or_create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Get existing folder ID or create it if missing."""
        existing_id = self.find_folder(name, parent_id=parent_id)
        if existing_id:
            return existing_id
        return self.create_folder(name, parent_id=parent_id)

    def upload_file(
        self,
        name: str,
        data: Union[bytes, io.BytesIO, io.BufferedReader],
        mime_type: str,
        parent_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a file to Google Drive.
        Accepts raw bytes, BytesIO stream, or file buffer.
        """
        service = self.get_service()
        file_metadata: Dict[str, Any] = {"name": name}
        if parent_id:
            file_metadata["parents"] = [parent_id]
        if description:
            file_metadata["description"] = description

        if isinstance(data, bytes):
            stream = io.BytesIO(data)
        elif isinstance(data, (io.BytesIO, io.BufferedReader)):
            stream = data
        else:
            stream = io.BytesIO(data)

        media = MediaIoBaseUpload(stream, mimetype=mime_type, resumable=True)
        file = (
            service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, name, mimeType, size, createdTime, modifiedTime",
            )
            .execute()
        )
        logger.info(f"Uploaded file '{name}' to Drive ID: {file.get('id')}")
        return file

    def update_file_content(
        self,
        file_id: str,
        data: Union[bytes, io.BytesIO, io.BufferedReader],
        mime_type: Optional[str] = None,
        new_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update existing file contents and optionally its name."""
        service = self.get_service()
        file_metadata = {}
        if new_name:
            file_metadata["name"] = new_name

        if isinstance(data, bytes):
            stream = io.BytesIO(data)
        elif isinstance(data, (io.BytesIO, io.BufferedReader)):
            stream = data
        else:
            stream = io.BytesIO(data)

        media = MediaIoBaseUpload(
            stream,
            mimetype=mime_type or "application/octet-stream",
            resumable=True,
        )
        updated_file = (
            service.files()
            .update(
                fileId=file_id,
                body=file_metadata if file_metadata else None,
                media_body=media,
                fields="id, name, mimeType, size, modifiedTime",
            )
            .execute()
        )
        logger.info(f"Updated file contents for Drive ID: {file_id}")
        return updated_file

    def download_file_bytes(self, file_id: str) -> bytes:
        """Download entire file into memory as bytes."""
        service = self.get_service()
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request, chunksize=1024 * 1024)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return fh.getvalue()

    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Retrieve metadata for a Drive file."""
        service = self.get_service()
        return (
            service.files()
            .get(
                fileId=file_id,
                fields="id, name, mimeType, size, createdTime, modifiedTime, description",
            )
            .execute()
        )

    def delete_file(self, file_id: str) -> bool:
        """Permanently delete or trash a file in Google Drive."""
        try:
            service = self.get_service()
            service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted Drive file ID: {file_id}")
            return True
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"File ID {file_id} already deleted or not found.")
                return True
            logger.error(f"Error deleting Drive file {file_id}: {e}")
            return False

    def read_json_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Read and parse a JSON document from Drive."""
        try:
            raw_bytes = self.download_file_bytes(file_id)
            text = raw_bytes.decode("utf-8")
            return json.loads(text)
        except Exception as e:
            logger.error(f"Failed to read/parse JSON from Drive file {file_id}: {e}")
            return None

    def write_json_file(
        self,
        file_id: Optional[str],
        data: Dict[str, Any],
        name: str = "content-index.json",
        parent_id: Optional[str] = None,
    ) -> str:
        """
        Write or update a JSON document in Drive.
        Returns the file ID.
        """
        json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        if file_id:
            try:
                self.update_file_content(
                    file_id=file_id,
                    data=json_bytes,
                    mime_type="application/json",
                )
                return file_id
            except HttpError as e:
                if e.resp.status != 404:
                    raise
                # If 404, fall through and create new
                logger.warning(f"File {file_id} not found when updating, recreating...")

        result = self.upload_file(
            name=name,
            data=json_bytes,
            mime_type="application/json",
            parent_id=parent_id,
            description="Antick Website CMS Content Index Manifest",
        )
        return result["id"]

    def read_text_file(self, file_id: str) -> str:
        """Read a UTF-8 text file (e.g. Markdown) from Drive."""
        raw_bytes = self.download_file_bytes(file_id)
        return raw_bytes.decode("utf-8")

    def write_text_file(
        self,
        file_id: Optional[str],
        content: str,
        name: str,
        parent_id: Optional[str] = None,
    ) -> str:
        """Write or update a UTF-8 text file (e.g. Markdown) in Drive."""
        text_bytes = content.encode("utf-8")
        if file_id:
            try:
                self.update_file_content(
                    file_id=file_id,
                    data=text_bytes,
                    mime_type="text/markdown",
                    new_name=name,
                )
                return file_id
            except HttpError as e:
                if e.resp.status != 404:
                    raise
                logger.warning(f"File {file_id} not found when updating, recreating...")

        result = self.upload_file(
            name=name,
            data=text_bytes,
            mime_type="text/markdown",
            parent_id=parent_id,
        )
        return result["id"]


# Global default instance
drive_service = GoogleDriveService()

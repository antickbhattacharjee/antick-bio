"""
Content Store Service for Antick Website CMS.
Maintains and manages persistent content records via Google Drive Metadata/content-index.json.
Provides in-memory TTL caching, atomic updates, schema validation, and search alias normalization.
NO SQL OR NOSQL DATABASE REQUIRED.
"""

import copy
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.google_drive import drive_service

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 120

CANONICAL_IDENTITY = {
    "canonical_name": "Antick Bhattacharjee",
    "search_aliases": [
        "Antik Bhattacharjee",
        "Antique Bhattacharjee",
        "Antick Bhattacharya",
    ],
}


class ContentStore:
    """In-memory cached manager for the Google Drive content index manifest."""

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self._cached_manifest: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0.0
        self._file_cache: Dict[str, bytes] = {}  # Optional in-memory cache for media bytes

    def _get_metadata_folder_id(self) -> Optional[str]:
        return os.environ.get("GOOGLE_DRIVE_METADATA_FOLDER_ID")

    def _get_manifest_file_id(self) -> Optional[str]:
        return os.environ.get("GOOGLE_DRIVE_MANIFEST_FILE_ID")

    def _set_manifest_file_id(self, file_id: str):
        os.environ["GOOGLE_DRIVE_MANIFEST_FILE_ID"] = file_id

    def get_default_manifest(self) -> Dict[str, Any]:
        """Return the clean baseline manifest structure without placeholder content."""
        return {
            "version": 1,
            "identity": copy.deepcopy(CANONICAL_IDENTITY),
            "photos": [],
            "videos": [],
            "literature": [],
        }

    def invalidate_cache(self):
        """Purge in-memory manifest cache to force fresh fetch on next read."""
        self._cached_manifest = None
        self._cache_timestamp = 0.0
        logger.info("ContentStore in-memory cache invalidated.")

    def _validate_and_sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all required keys exist and schema conforms to version 1."""
        if not isinstance(data, dict):
            data = self.get_default_manifest()

        if "version" not in data:
            data["version"] = 1
        if "identity" not in data:
            data["identity"] = copy.deepcopy(CANONICAL_IDENTITY)
        if "photos" not in data or not isinstance(data["photos"], list):
            data["photos"] = []
        if "videos" not in data or not isinstance(data["videos"], list):
            data["videos"] = []
        if "literature" not in data or not isinstance(data["literature"], list):
            data["literature"] = []

        return data

    def load_manifest(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Load the content-index manifest.
        Uses in-memory TTL caching when possible.
        Falls back to default manifest if Drive is not yet configured.
        """
        now = time.time()
        if (
            not force_refresh
            and self._cached_manifest is not None
            and (now - self._cache_timestamp) < self.ttl_seconds
        ):
            return copy.deepcopy(self._cached_manifest)

        manifest = None

        if drive_service.is_configured:
            manifest_file_id = self._get_manifest_file_id()
            metadata_folder_id = self._get_metadata_folder_id()

            # If manifest_file_id not in environment, try finding content-index.json
            if not manifest_file_id and metadata_folder_id:
                try:
                    service = drive_service.get_service()
                    query = (
                        f"name = 'content-index.json' and '{metadata_folder_id}' in parents and trashed = false"
                    )
                    res = service.files().list(q=query, fields="files(id, name)", pageSize=1).execute()
                    files = res.get("files", [])
                    if files:
                        manifest_file_id = files[0]["id"]
                        self._set_manifest_file_id(manifest_file_id)
                except Exception as e:
                    logger.warning(f"Could not query Drive for content-index.json: {e}")

            if manifest_file_id:
                try:
                    manifest = drive_service.read_json_file(manifest_file_id)
                except Exception as e:
                    logger.error(f"Error reading manifest file from Drive: {e}")

        if manifest is None:
            # If still None, check if we have cached copy or use default
            if self._cached_manifest is not None:
                manifest = self._cached_manifest
            else:
                manifest = self.get_default_manifest()

        sanitized = self._validate_and_sanitize(manifest)
        self._cached_manifest = sanitized
        self._cache_timestamp = now
        return copy.deepcopy(sanitized)

    def save_manifest(self, manifest_data: Dict[str, Any]) -> bool:
        """
        Atomically persist manifest to Google Drive and update in-memory cache.
        """
        sanitized = self._validate_and_sanitize(manifest_data)

        if drive_service.is_configured:
            try:
                manifest_file_id = self._get_manifest_file_id()
                metadata_folder_id = self._get_metadata_folder_id()

                new_file_id = drive_service.write_json_file(
                    file_id=manifest_file_id,
                    data=sanitized,
                    name="content-index.json",
                    parent_id=metadata_folder_id,
                )
                self._set_manifest_file_id(new_file_id)
            except Exception as e:
                logger.error(f"Failed to persist manifest to Google Drive: {e}")
                # Keep local cached update even if remote write failed
                self._cached_manifest = sanitized
                self._cache_timestamp = time.time()
                return False

        self._cached_manifest = sanitized
        self._cache_timestamp = time.time()
        logger.info("Manifest saved and cache updated.")
        return True

    # -------------------------------------------------------------------------
    # Photo Management
    # -------------------------------------------------------------------------

    def get_photos(self, published_only: bool = True) -> List[Dict[str, Any]]:
        manifest = self.load_manifest()
        photos = manifest.get("photos", [])
        if published_only:
            photos = [p for p in photos if p.get("published", True)]
        # Sort by date / created_at descending
        return sorted(photos, key=lambda x: x.get("created_at", ""), reverse=True)

    def get_photo_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        manifest = self.load_manifest()
        for p in manifest.get("photos", []):
            if p.get("slug") == slug:
                return p
        return None

    def get_photo_by_id(self, photo_id: str) -> Optional[Dict[str, Any]]:
        manifest = self.load_manifest()
        for p in manifest.get("photos", []):
            if p.get("id") == photo_id:
                return p
        return None

    def get_primary_profile_photo(self) -> Optional[Dict[str, Any]]:
        """Return the designated primary profile photo record."""
        photos = self.get_photos(published_only=True)
        for p in photos:
            if p.get("primary_profile"):
                return p
        return photos[0] if photos else None

    def save_photo(self, photo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a photo record."""
        manifest = self.load_manifest()
        photos = manifest.get("photos", [])

        if not photo_data.get("id"):
            photo_data["id"] = str(uuid.uuid4())
            photo_data["created_at"] = datetime.utcnow().isoformat()
        photo_data["updated_at"] = datetime.utcnow().isoformat()

        # If this photo is set to primary_profile, unset all other photos
        if photo_data.get("primary_profile"):
            for p in photos:
                if p.get("id") != photo_data["id"]:
                    p["primary_profile"] = False

        existing_idx = next((i for i, p in enumerate(photos) if p.get("id") == photo_data["id"]), None)
        if existing_idx is not None:
            photos[existing_idx] = photo_data
        else:
            photos.append(photo_data)

        manifest["photos"] = photos
        self.save_manifest(manifest)
        return photo_data

    def delete_photo(self, photo_id: str, delete_drive_file: bool = True) -> bool:
        manifest = self.load_manifest()
        photos = manifest.get("photos", [])
        photo = next((p for p in photos if p.get("id") == photo_id), None)
        if not photo:
            return False

        if delete_drive_file and photo.get("drive_file_id") and drive_service.is_configured:
            try:
                drive_service.delete_file(photo["drive_file_id"])
            except Exception as e:
                logger.warning(f"Could not delete drive file {photo.get('drive_file_id')}: {e}")

        manifest["photos"] = [p for p in photos if p.get("id") != photo_id]
        self.save_manifest(manifest)
        return True

    # -------------------------------------------------------------------------
    # Video Management
    # -------------------------------------------------------------------------

    def get_videos(self, published_only: bool = True) -> List[Dict[str, Any]]:
        manifest = self.load_manifest()
        videos = manifest.get("videos", [])
        if published_only:
            videos = [v for v in videos if v.get("published", True)]
        return sorted(videos, key=lambda x: x.get("created_at", ""), reverse=True)

    def get_video_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        manifest = self.load_manifest()
        for v in manifest.get("videos", []):
            if v.get("slug") == slug:
                return v
        return None

    def get_video_by_id(self, video_id: str) -> Optional[Dict[str, Any]]:
        manifest = self.load_manifest()
        for v in manifest.get("videos", []):
            if v.get("id") == video_id:
                return v
        return None

    def save_video(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        manifest = self.load_manifest()
        videos = manifest.get("videos", [])

        if not video_data.get("id"):
            video_data["id"] = str(uuid.uuid4())
            video_data["created_at"] = datetime.utcnow().isoformat()
        video_data["updated_at"] = datetime.utcnow().isoformat()

        existing_idx = next((i for i, v in enumerate(videos) if v.get("id") == video_data["id"]), None)
        if existing_idx is not None:
            videos[existing_idx] = video_data
        else:
            videos.append(video_data)

        manifest["videos"] = videos
        self.save_manifest(manifest)
        return video_data

    def delete_video(self, video_id: str, delete_drive_file: bool = True) -> bool:
        manifest = self.load_manifest()
        videos = manifest.get("videos", [])
        video = next((v for v in videos if v.get("id") == video_id), None)
        if not video:
            return False

        if delete_drive_file and drive_service.is_configured:
            if video.get("drive_file_id"):
                try:
                    drive_service.delete_file(video["drive_file_id"])
                except Exception as e:
                    logger.warning(f"Could not delete drive video file {video.get('drive_file_id')}: {e}")
            if video.get("poster_drive_file_id"):
                try:
                    drive_service.delete_file(video["poster_drive_file_id"])
                except Exception as e:
                    logger.warning(f"Could not delete drive poster file: {e}")

        manifest["videos"] = [v for v in videos if v.get("id") != video_id]
        self.save_manifest(manifest)
        return True

    # -------------------------------------------------------------------------
    # Literature Management
    # -------------------------------------------------------------------------

    def get_literature(self, published_only: bool = True) -> List[Dict[str, Any]]:
        manifest = self.load_manifest()
        literature = manifest.get("literature", [])
        if published_only:
            literature = [lit for lit in literature if lit.get("published", True)]
        return sorted(
            literature,
            key=lambda x: x.get("publication_date") or x.get("created_at", ""),
            reverse=True,
        )

    def get_literature_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        manifest = self.load_manifest()
        for lit in manifest.get("literature", []):
            if lit.get("slug") == slug:
                return lit
        return None

    def get_literature_by_id(self, lit_id: str) -> Optional[Dict[str, Any]]:
        manifest = self.load_manifest()
        for lit in manifest.get("literature", []):
            if lit.get("id") == lit_id:
                return lit
        return None

    def save_literature(self, lit_data: Dict[str, Any], body_markdown: Optional[str] = None) -> Dict[str, Any]:
        """
        Save literature metadata to content-index.json and store body as .md in Drive / Literature.
        """
        manifest = self.load_manifest()
        literature = manifest.get("literature", [])

        if not lit_data.get("id"):
            lit_data["id"] = str(uuid.uuid4())
            lit_data["created_at"] = datetime.utcnow().isoformat()
        lit_data["updated_at"] = datetime.utcnow().isoformat()

        # If body_markdown is provided and Drive is configured, save UTF-8 Markdown file
        if body_markdown is not None and drive_service.is_configured:
            lit_folder_id = os.environ.get("GOOGLE_DRIVE_LITERATURE_FOLDER_ID")
            md_filename = f"{lit_data['slug']}.md"
            file_id = lit_data.get("drive_file_id")
            new_file_id = drive_service.write_text_file(
                file_id=file_id,
                content=body_markdown,
                name=md_filename,
                parent_id=lit_folder_id,
            )
            lit_data["drive_file_id"] = new_file_id

        existing_idx = next((i for i, lit in enumerate(literature) if lit.get("id") == lit_data["id"]), None)
        if existing_idx is not None:
            literature[existing_idx] = lit_data
        else:
            literature.append(lit_data)

        manifest["literature"] = literature
        self.save_manifest(manifest)
        return lit_data

    def get_literature_body(self, lit_record: Dict[str, Any]) -> str:
        """Fetch full markdown body from Drive or fallback record."""
        file_id = lit_record.get("drive_file_id")
        if file_id and drive_service.is_configured:
            try:
                return drive_service.read_text_file(file_id)
            except Exception as e:
                logger.error(f"Error reading literature body for {lit_record.get('slug')}: {e}")
        return lit_record.get("body", "")

    def delete_literature(self, lit_id: str, delete_drive_file: bool = True) -> bool:
        manifest = self.load_manifest()
        literature = manifest.get("literature", [])
        lit = next((l for l in literature if l.get("id") == lit_id), None)
        if not lit:
            return False

        if delete_drive_file and lit.get("drive_file_id") and drive_service.is_configured:
            try:
                drive_service.delete_file(lit["drive_file_id"])
            except Exception as e:
                logger.warning(f"Could not delete drive markdown file: {e}")

        manifest["literature"] = [l for l in literature if l.get("id") != lit_id]
        self.save_manifest(manifest)
        return True

    # -------------------------------------------------------------------------
    # Search & Alias Normalization
    # -------------------------------------------------------------------------

    def search_content(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform lightweight site search across photos, videos, and literature.
        Normalizes aliases (e.g. 'antik', 'antique' -> 'antick').
        """
        if not query or not query.strip():
            return {"photos": [], "videos": [], "literature": []}

        q = query.strip().lower()

        # Check aliases to normalize query
        for alias in CANONICAL_IDENTITY["search_aliases"]:
            alias_clean = alias.lower()
            if alias_clean in q:
                q = q.replace(alias_clean, "antick bhattacharjee")
            first_name_alias = alias.split()[0].lower()
            if first_name_alias in q:
                q = q.replace(first_name_alias, "antick")

        terms = q.split()

        def matches(text: str) -> bool:
            if not text:
                return False
            text_lower = text.lower()
            return any(t in text_lower for t in terms)

        photos = self.get_photos(published_only=True)
        matched_photos = [
            p for p in photos
            if matches(p.get("title", ""))
            or matches(p.get("description", ""))
            or matches(p.get("caption", ""))
            or matches(" ".join(p.get("tags", [])))
            or matches(p.get("category", ""))
        ]

        videos = self.get_videos(published_only=True)
        matched_videos = [
            v for v in videos
            if matches(v.get("title", ""))
            or matches(v.get("description", ""))
            or matches(" ".join(v.get("tags", [])))
            or matches(v.get("category", ""))
        ]

        literature = self.get_literature(published_only=True)
        matched_lit = [
            l for l in literature
            if matches(l.get("title", ""))
            or matches(l.get("short_description", ""))
            or matches(" ".join(l.get("tags", [])))
            or matches(l.get("content_type", ""))
        ]

        return {
            "photos": matched_photos,
            "videos": matched_videos,
            "literature": matched_lit,
        }


# Global default instance
content_store = ContentStore()

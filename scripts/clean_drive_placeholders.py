"""
Clean all demo and placeholder content from Google Drive and reset content-index.json.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from app.services.google_drive import drive_service
from app.services.content_store import CANONICAL_IDENTITY, content_store

clean_manifest = {
    "version": 1,
    "identity": CANONICAL_IDENTITY,
    "photos": [],
    "videos": [],
    "literature": [],
}


def main():
    print("==================================================")
    print("Antick Website CMS — Clean Placeholders")
    print("==================================================")

    if drive_service.is_configured:
        print("Connecting to Google Drive...")
        service = drive_service.get_service()

        meta_folder_id = os.environ.get("GOOGLE_DRIVE_METADATA_FOLDER_ID")
        manifest_file_id = os.environ.get("GOOGLE_DRIVE_MANIFEST_FILE_ID")

        # Update content-index.json
        new_id = drive_service.write_json_file(
            file_id=manifest_file_id,
            data=clean_manifest,
            name="content-index.json",
            parent_id=meta_folder_id,
        )
        print(f"[OK] Google Drive content-index.json reset to empty arrays. File ID: {new_id}")

        # Delete any test/demo files in Photos, Videos, Literature folders
        folder_env_keys = [
            ("Photos", "GOOGLE_DRIVE_PHOTOS_FOLDER_ID"),
            ("Videos", "GOOGLE_DRIVE_VIDEOS_FOLDER_ID"),
            ("Literature", "GOOGLE_DRIVE_LITERATURE_FOLDER_ID"),
        ]

        for folder_name, key in folder_env_keys:
            folder_id = os.environ.get(key)
            if folder_id:
                query = f"'{folder_id}' in parents and trashed = false"
                res = service.files().list(q=query, fields="files(id, name)").execute()
                for f in res.get("files", []):
                    print(f"  [Deleted Drive File] {folder_name}/{f['name']} (ID: {f['id']})")
                    service.files().delete(fileId=f["id"]).execute()
    else:
        print("[NOTE] Drive not currently configured in local environment; resetting local cache.")

    content_store.save_manifest(clean_manifest)
    content_store.invalidate_cache()
    print("[OK] Local manifest cache reset.")
    print("==================================================")
    print("Placeholder removal complete!")
    print("==================================================")


if __name__ == "__main__":
    main()

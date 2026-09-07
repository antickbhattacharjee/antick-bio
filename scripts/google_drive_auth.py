"""
Google Drive OAuth Desktop Client Authorization & CMS Initialization Script.
Handles one-time interactive OAuth setup for Antick Website CMS.
Scope: https://www.googleapis.com/auth/drive.file
Creates private Drive folders, content manifest, admin password hash, and .env configuration.
"""

import glob
import json
import os
import secrets
import string
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from werkzeug.security import generate_password_hash

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def find_oauth_client_json(root_dir: Path) -> Path:
    """Safely discover Google OAuth Desktop client JSON in root directory."""
    candidate_patterns = [
        "google_oauth_client.json",
        "client_secret*.json",
        "credentials*.json",
        "oauth*.json",
        "*.json",
    ]

    for pattern in candidate_patterns:
        for file_path in root_dir.glob(pattern):
            if file_path.name in ("package.json", "tsconfig.json", "content-index.json", "token.json"):
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Desktop client JSON typically has "installed" root key
                        if "installed" in data:
                            inst = data["installed"]
                            if "client_id" in inst and "client_secret" in inst:
                                return file_path
                        # Web client JSON has "web" root key
                        elif "web" in data:
                            web = data["web"]
                            if "client_id" in web and "client_secret" in web:
                                return file_path
            except Exception:
                continue

    raise FileNotFoundError(
        "Could not find a valid Google OAuth Client Secrets JSON file in the project root. "
        "Please ensure your OAuth Desktop credentials JSON is placed in the project root."
    )


def generate_temp_password(length: int = 16) -> str:
    """Generate cryptographically secure temporary password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%^&*" for c in password)
        ):
            return password


def load_existing_env(env_path: Path) -> dict:
    """Parse existing .env file if present."""
    env_vars = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip("'\"")
    return env_vars


def main():
    print("==================================================")
    print("Antick Website CMS — Google Drive OAuth Setup")
    print("==================================================")

    # 1. Locate OAuth JSON
    oauth_json_path = find_oauth_client_json(PROJECT_ROOT)
    print(f"[OK] Located OAuth Client JSON: {oauth_json_path.name}")

    with open(oauth_json_path, "r", encoding="utf-8") as f:
        client_data = json.load(f)
        section = client_data.get("installed") or client_data.get("web", {})
        client_id = section.get("client_id")
        client_secret = section.get("client_secret")

    if not client_id or not client_secret:
        print("[ERROR] client_id or client_secret missing from OAuth JSON.")
        sys.exit(1)

    # 2. Interactive OAuth Flow
    print("\nStarting interactive Google OAuth authorization...")
    print(f"Requesting scope: {SCOPES[0]}")
    flow = InstalledAppFlow.from_client_secrets_file(
        str(oauth_json_path),
        scopes=SCOPES,
    )

    try:
        # Run local server to catch redirect
        credentials = flow.run_local_server(
            port=0,
            access_type="offline",
            prompt="consent",
            success_message="Google Drive Authorization Successful! You can close this browser tab.",
        )
    except Exception as e:
        print(f"[WARNING] Local server authorization failed: {e}")
        print("Attempting console flow...")
        credentials = flow.run_console(access_type="offline", prompt="consent")

    refresh_token = credentials.refresh_token
    if not refresh_token:
        print(
            "[WARNING] No refresh token returned. This can happen if consent was already granted. "
            "Please ensure prompt='consent' was used."
        )

    # 3. Test Drive Connection & Build CMS Directory Tree
    print("\nTesting Google Drive API connection...")
    service = build("drive", "v3", credentials=credentials, cache_discovery=False)

    def get_or_create(folder_name: str, parent_id: str = None) -> str:
        q = f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}' and trashed = false"
        if parent_id:
            q += f" and '{parent_id}' in parents"
        res = service.files().list(q=q, spaces="drive", fields="files(id, name)").execute()
        files = res.get("files", [])
        if files:
            print(f"  [Found Folder] {folder_name} (ID: {files[0]['id']})")
            return files[0]["id"]
        meta = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            meta["parents"] = [parent_id]
        created = service.files().create(body=meta, fields="id, name").execute()
        print(f"  [Created Folder] {folder_name} (ID: {created['id']})")
        return created["id"]

    print("\nCreating/Verifying Google Drive CMS Folder Structure:")
    root_folder_id = get_or_create("Antick Website CMS")
    photos_folder_id = get_or_create("Photos", parent_id=root_folder_id)
    videos_folder_id = get_or_create("Videos", parent_id=root_folder_id)
    lit_folder_id = get_or_create("Literature", parent_id=root_folder_id)
    meta_folder_id = get_or_create("Metadata", parent_id=root_folder_id)

    # 4. Initialize Metadata/content-index.json if missing
    q_manifest = f"name = 'content-index.json' and '{meta_folder_id}' in parents and trashed = false"
    res_manifest = service.files().list(q=q_manifest, fields="files(id, name)").execute()
    manifest_files = res_manifest.get("files", [])

    if not manifest_files:
        print("\nCreating initial Metadata/content-index.json in Google Drive...")
        from app.gallery_data import GALLERY_IMAGES

        initial_photos = []
        for i, img in enumerate(GALLERY_IMAGES, 1):
            initial_photos.append({
                "id": f"seed-photo-{i:03d}",
                "drive_file_id": "",
                "local_fallback_path": img.get("relative_path"),
                "slug": img.get("slug"),
                "filename": img.get("filename"),
                "mime_type": "image/webp",
                "width": img.get("width", 1200),
                "height": img.get("height", 800),
                "title": img.get("title"),
                "description": img.get("description"),
                "alt_text": img.get("alt"),
                "caption": img.get("caption"),
                "category": img.get("category", "General"),
                "category_slug": img.get("category_slug", "general"),
                "tags": [img.get("category_slug", "general")],
                "date": img.get("date", "2026"),
                "location": "West Bengal, India",
                "featured": img.get("featured", True),
                "primary_profile": img.get("is_primary_profile", False),
                "published": True,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            })

        initial_manifest = {
            "version": 1,
            "identity": {
                "canonical_name": "Antick Bhattacharjee",
                "search_aliases": [
                    "Antik Bhattacharjee",
                    "Antique Bhattacharjee",
                    "Antick Bhattacharya",
                ],
            },
            "photos": initial_photos,
            "videos": [],
            "literature": [
                {
                    "id": "seed-lit-001",
                    "drive_file_id": "",
                    "slug": "first-principles-in-programming",
                    "title": "The Value of First-Principles Learning in Programming",
                    "content_type": "Essay",
                    "short_description": "Why understanding foundational computing and architecture beats chasing fleeting framework trends every single time.",
                    "body": "# The Value of First-Principles Learning in Programming\n\nBy **Antick Bhattacharjee**\n\nWhen exploring software engineering, frameworks and libraries come and go with incredible speed. However, core computing principles—data structures, networking fundamentals, memory management, and asynchronous flow—remain stable across decades.\n\nLearning from first principles enables an engineer to debug complex production issues, adapt rapidly to emerging paradigms, and architect dependable systems without cargo-culting.",
                    "tags": ["Technology", "Education", "Engineering"],
                    "featured": True,
                    "published": True,
                    "publication_date": "2026-01-15",
                    "created_at": "2026-01-15T00:00:00Z",
                    "updated_at": "2026-01-15T00:00:00Z",
                },
                {
                    "id": "seed-lit-002",
                    "drive_file_id": "",
                    "slug": "pragmatic-automation-where-to-start",
                    "title": "Pragmatic Automation: Where to Start in Your Workflow",
                    "content_type": "Thought",
                    "short_description": "A systematic approach to identifying repetitive tasks and building dependable scripts that save hours every week.",
                    "body": "# Pragmatic Automation: Where to Start in Your Workflow\n\nBy **Antick Bhattacharjee**\n\nAutomation is most valuable when applied with precision to high-frequency, deterministic tasks. Before writing code, audit your daily operations:\n\n1. **Identify Repetitive Friction**: Look for spreadsheet copying, repetitive email reports, or manual data transforms.\n2. **Isolate Inputs and Outputs**: Build small, testable Python scripts that do one thing reliably.\n3. **Fail Safely**: Ensure automated jobs log errors gracefully without corrupting existing data.",
                    "tags": ["Automation", "Python", "Productivity"],
                    "featured": True,
                    "published": True,
                    "publication_date": "2026-02-01",
                    "created_at": "2026-02-01T00:00:00Z",
                    "updated_at": "2026-02-01T00:00:00Z",
                },
            ],
        }

        from googleapiclient.http import MediaInMemoryUpload
        manifest_bytes = json.dumps(initial_manifest, indent=2, ensure_ascii=False).encode("utf-8")
        media = MediaInMemoryUpload(manifest_bytes, mimetype="application/json")
        meta_body = {
            "name": "content-index.json",
            "parents": [meta_folder_id],
            "description": "Antick Website CMS Content Index Manifest",
        }
        manifest_file = service.files().create(body=meta_body, media_body=media, fields="id").execute()
        manifest_file_id = manifest_file["id"]
        print(f"  [OK] Initial content-index.json created (ID: {manifest_file_id})")
    else:
        manifest_file_id = manifest_files[0]["id"]
        print(f"  [OK] Found existing content-index.json (ID: {manifest_file_id})")

    # 5. Environment & Admin Credentials
    env_path = PROJECT_ROOT / ".env"
    existing_env = load_existing_env(env_path)

    secret_key = existing_env.get("SECRET_KEY") or secrets.token_hex(32)
    admin_user = existing_env.get("ADMIN_USERNAME") or "antick"
    admin_pw_hash = existing_env.get("ADMIN_PASSWORD_HASH")

    temp_password = None
    if not admin_pw_hash:
        temp_password = generate_temp_password(16)
        admin_pw_hash = generate_password_hash(temp_password)

    env_content = f"""# Auto-generated by scripts/google_drive_auth.py
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY={secret_key}
ADMIN_USERNAME={admin_user}
ADMIN_PASSWORD_HASH={admin_pw_hash}

GOOGLE_CLIENT_ID={client_id}
GOOGLE_CLIENT_SECRET={client_secret}
GOOGLE_REFRESH_TOKEN={refresh_token or existing_env.get('GOOGLE_REFRESH_TOKEN', '')}

GOOGLE_DRIVE_ROOT_FOLDER_ID={root_folder_id}
GOOGLE_DRIVE_PHOTOS_FOLDER_ID={photos_folder_id}
GOOGLE_DRIVE_VIDEOS_FOLDER_ID={videos_folder_id}
GOOGLE_DRIVE_LITERATURE_FOLDER_ID={lit_folder_id}
GOOGLE_DRIVE_METADATA_FOLDER_ID={meta_folder_id}
GOOGLE_DRIVE_MANIFEST_FILE_ID={manifest_file_id}

MAX_IMAGE_UPLOAD_MB=15
MAX_VIDEO_UPLOAD_MB=150
"""

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)
    print("\n[OK] Local .env written securely.")

    # 6. Generate render-env.txt (Git-ignored helper)
    render_env_path = PROJECT_ROOT / "render-env.txt"
    render_env_content = f"""# Render Production Environment Variables
# Copy these values into Render Dashboard -> Environment Variables

SECRET_KEY={secret_key}
ADMIN_USERNAME={admin_user}
ADMIN_PASSWORD_HASH={admin_pw_hash}

GOOGLE_CLIENT_ID={client_id}
GOOGLE_CLIENT_SECRET={client_secret}
GOOGLE_REFRESH_TOKEN={refresh_token or existing_env.get('GOOGLE_REFRESH_TOKEN', '')}

GOOGLE_DRIVE_ROOT_FOLDER_ID={root_folder_id}
GOOGLE_DRIVE_PHOTOS_FOLDER_ID={photos_folder_id}
GOOGLE_DRIVE_VIDEOS_FOLDER_ID={videos_folder_id}
GOOGLE_DRIVE_LITERATURE_FOLDER_ID={lit_folder_id}
GOOGLE_DRIVE_METADATA_FOLDER_ID={meta_folder_id}
GOOGLE_DRIVE_MANIFEST_FILE_ID={manifest_file_id}

MAX_IMAGE_UPLOAD_MB=15
MAX_VIDEO_UPLOAD_MB=150
"""
    with open(render_env_path, "w", encoding="utf-8") as f:
        f.write(render_env_content)
    print("[OK] Local render-env.txt generated for Render deployment.")

    print("\n==================================================")
    print("Google Drive CMS Setup Complete!")
    print("==================================================")
    print(f"Admin Username: {admin_user}")
    if temp_password:
        print(f"Temporary Admin Password (ONE-TIME DISPLAY): {temp_password}")
        print("NOTE: Please log in at /admin and change this password under Settings.")
    else:
        print("Admin password hash preserved from existing configuration.")
    print("==================================================")


if __name__ == "__main__":
    main()

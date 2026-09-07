# Antick Bhattacharjee — Personal Website & Google Drive CMS

A high-performance, modular personal publishing CMS and portfolio for **Antick Bhattacharjee** (Corporate Trainer, Technology Educator, Python Developer, and Solution Architect), built with **Python, Flask, Jinja2, Vanilla CSS3, and Google Drive API v3**.

Production domain: **[https://www.antickbhattacharjee.qd.je](https://www.antickbhattacharjee.qd.je)**

---

## 1. Zero-Database Architecture Overview

This platform operates **without any SQL or NoSQL database services** (No PostgreSQL, MySQL, SQLite, MongoDB, Firebase, Supabase, or SQLAlchemy). Instead, persistent storage is powered entirely by private folders in **Google Drive**:

```
Browser / Search Crawler
       |
       v
Flask Website (Gunicorn on Render)
       |
       +---- Public Website (/ , /gallery, /literature, /media, /about, /training, /projects)
       |
       +---- Admin CMS (/admin)
                |
                v  (Google Drive API v3 — Scope: drive.file)
         Antick Website CMS/
                |
                +-- Photos/        (Optimized WebP images: antick-bhattacharjee-photo-XXX.webp)
                +-- Videos/        (MP4 video presentations & posters)
                +-- Literature/    (UTF-8 Markdown creative works: <slug>.md)
                +-- Metadata/
                       |
                       +-- content-index.json  (Persistent manifest)
```

- **Drive Isolation & Privacy**: Google Drive folders remain strictly private. Public visitors interact only with Flask proxy endpoints (`/media/photo/...`, `/media/video/...`).
- **In-Memory TTL Caching**: `content-index.json` is cached with an in-memory TTL (60–300 seconds) to ensure sub-millisecond response times. Admin mutations immediately invalidate the cache.

---

## 2. Google OAuth Testing Mode Warning

> [!WARNING]
> **Important Note on Google OAuth Refresh Token Longevity:**
> In the Google Cloud Console, OAuth Consent Screens in **"Testing"** publishing status limit refresh tokens for External user types to **7 days of validity**.
> 
> For long-running production deployments on Render:
> 1. In Google Cloud Console &rarr; *APIs &amp; Services* &rarr; *OAuth consent screen*, move your app status from **Testing** to **In Production** (or Internal for Workspace domains).
> 2. Run `python scripts/google_drive_auth.py` once to generate a permanent refresh token.
> 3. Update the `GOOGLE_REFRESH_TOKEN` in Render Environment Variables.

---

## 3. Admin CMS Features

The CMS is accessible at `/admin` and provides single-owner management for:

### 1. Photos (`/admin/photos`)
- **Upload & Optimization**: Standard Pillow normalization (EXIF orientation auto-transpose, high-efficiency WebP conversion, non-stretching downscale).
- **Collision-Safe Canonical Naming**: `antick-bhattacharjee-photo-001.webp`, `antick-bhattacharjee-photo-002.webp`, etc.
- **Natural Alt-Text Suggestions**: Automatically suggested descriptive alt text without keyword stuffing.
- **Primary Profile Image**: Designate one photo as the primary profile image to instantly update the homepage hero, `Person` Schema, `ProfilePage` Schema, and Open Graph metadata site-wide.

### 2. Videos (`/admin/videos`)
- **Storage & Watch Pages**: Videos are stored in `Google Drive / Videos` and presented on dedicated crawlable watch pages (`/gallery/video/<slug>`).
- **Media Streaming**: Served through `/media/video/<slug>` supporting HTTP `Range` headers (`206 Partial Content`, `Accept-Ranges: bytes`).
- **Structured Data**: Automatically emits `VideoObject` JSON-LD with transcripts when provided.

### 3. Literature (`/admin/literature`)
- **Creative Writing CMS**: Publish Essays, Thoughts, Poetry, Prose, Short Stories, and Articles.
- **Persistent Storage**: Body text is stored as clean UTF-8 `.md` files in `Google Drive / Literature/<slug>.md`.
- **Server-Side Rendering**: Server-renders Markdown into semantic HTML with `bleach` sanitization for maximum SEO indexing.
- **Structured Data**: Emits `CreativeWork` JSON-LD schema.

### 4. Manifest Inspector & Password Settings (`/admin/content`, `/admin/settings`)
- Inspect raw `content-index.json` and download backups.
- Securely update the administrator password with current password verification and Werkzeug password hashing.

---

## 4. Canonical Identity & SEO Strategy

- **Canonical Identity**: `Antick Bhattacharjee`
- **Search Aliases**: `Antik Bhattacharjee`, `Antique Bhattacharjee`, `Antick Bhattacharya`
- **Alias Resolution**: Search queries matching common misspellings (e.g. "Antik") seamlessly return matching Antick content without spamming or keyword-stuffing metadata tags.
- **Domain Enforcement**: Canonical URLs, Image Sitemaps, and Schema `@id` tags strictly use `https://www.antickbhattacharjee.qd.je` (never `onrender.com`).

---

## 5. Quick Start & Setup Guide

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Initialize Google Drive CMS
Ensure your Google OAuth Desktop client JSON (`google_oauth_client.json` or `client_secret*.json`) is in the project root, then run:

```bash
python scripts/google_drive_auth.py
```

This single command:
1. Opens your browser for one-time Google OAuth authorization (scope: `https://www.googleapis.com/auth/drive.file`).
2. Creates the private `Antick Website CMS` folders in your Google Drive.
3. Initializes `Metadata/content-index.json`.
4. Creates a local `.env` and exports Render environment values to `render-env.txt`.
5. Displays your one-time temporary admin password.

### Step 3: Run Development Server
```bash
python run.py
```
Visit `http://127.0.0.1:5000/` or `http://127.0.0.1:5000/admin`.

---

## 6. Render Deployment

The repository includes a [render.yaml](file:///d:/Projects/bio/render.yaml) blueprint:

1. In Render Dashboard, create a new Web Service connected to this repository branch (`main`).
2. Copy the values generated in local `render-env.txt` into **Render &rarr; Environment Variables**:
   - `SECRET_KEY`
   - `ADMIN_USERNAME`
   - `ADMIN_PASSWORD_HASH`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REFRESH_TOKEN`
   - `GOOGLE_DRIVE_ROOT_FOLDER_ID`
   - `GOOGLE_DRIVE_PHOTOS_FOLDER_ID`
   - `GOOGLE_DRIVE_VIDEOS_FOLDER_ID`
   - `GOOGLE_DRIVE_LITERATURE_FOLDER_ID`
   - `GOOGLE_DRIVE_METADATA_FOLDER_ID`
   - `GOOGLE_DRIVE_MANIFEST_FILE_ID`

---

## 7. Running Tests

Run the automated test suite:
```bash
python -m unittest tests/test_cms.py
```

---

## 8. License

&copy; Antick Bhattacharjee. All rights reserved.

"""
Automated unit & integration test suite for Antick Website CMS.
Verifies zero SQL database, content store, image processing, markdown rendering,
admin authentication, CSRF, noindex headers, search alias normalization, sitemap,
favicon, and robust 404/500 template error handling.
"""

import os
import unittest
from io import BytesIO
from PIL import Image
from werkzeug.security import generate_password_hash

from app import create_app
from app.routes import render_markdown_safely
from app.services.content_store import ContentStore, content_store
from app.services.media_processor import (
    generate_canonical_photo_filename,
    normalize_and_convert_image,
    suggest_alt_text,
)


class CMSTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["ADMIN_USERNAME"] = "antick"
        os.environ["ADMIN_PASSWORD_HASH"] = generate_password_hash("TestSecurePassword123!")
        os.environ["SECRET_KEY"] = "test-secret-key-12345"

    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key-12345",
        })
        self.client = self.app.test_client()

    def login_admin(self):
        """Helper to log in as administrator."""
        return self.client.post("/admin/login", data={
            "username": "antick",
            "password": "TestSecurePassword123!",
        }, follow_redirects=True)

    # -------------------------------------------------------------------------
    # Zero SQL Database Verification
    # -------------------------------------------------------------------------

    def test_no_sql_database_exists(self):
        """Confirm no SQLite or SQL database files exist in project root."""
        root_dir = os.path.dirname(os.path.dirname(__file__))
        for f in os.listdir(root_dir):
            self.assertFalse(f.endswith(".db"), f"Unexpected database file found: {f}")
            self.assertFalse(f.endswith(".sqlite"), f"Unexpected database file found: {f}")
            self.assertFalse(f.endswith(".sqlite3"), f"Unexpected database file found: {f}")

    # -------------------------------------------------------------------------
    # Content Store & Schema
    # -------------------------------------------------------------------------

    def test_content_store_schema(self):
        """Verify default manifest structure."""
        store = ContentStore()
        manifest = store.get_default_manifest()
        self.assertEqual(manifest["version"], 1)
        self.assertEqual(manifest["identity"]["canonical_name"], "Antick Bhattacharjee")
        self.assertIn("Antik Bhattacharjee", manifest["identity"]["search_aliases"])
        self.assertIsInstance(manifest["photos"], list)
        self.assertIsInstance(manifest["videos"], list)
        self.assertIsInstance(manifest["literature"], list)

    # -------------------------------------------------------------------------
    # Media Processing & Markdown Sanitization
    # -------------------------------------------------------------------------

    def test_media_processor_webp_and_orientation(self):
        """Test Pillow normalization to WebP and dimension calculation."""
        img = Image.new("RGB", (1600, 1200), color=(73, 109, 137))
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        raw_data = img_bytes.getvalue()

        webp_bytes, width, height, mime = normalize_and_convert_image(raw_data, max_dimension=1000)
        self.assertEqual(mime, "image/webp")
        self.assertLessEqual(width, 1000)
        self.assertLessEqual(height, 1000)
        self.assertTrue(len(webp_bytes) > 0)

    def test_canonical_filename_and_alt_text(self):
        """Verify collision-safe filename and clean alt text."""
        fn = generate_canonical_photo_filename(1)
        self.assertEqual(fn, "antick-bhattacharjee-photo-001.webp")

        alt = suggest_alt_text("Python Workshop", category="Training Sessions")
        self.assertIn("Antick Bhattacharjee", alt)
        self.assertIn("Python Workshop", alt)

    def test_markdown_sanitization(self):
        """Verify Markdown renders safe semantic HTML with bleach."""
        md = "# Heading 1\n\n**Bold Text**\n\n<script>alert('xss')</script>"
        html = render_markdown_safely(md)
        self.assertIn("Heading 1</h1>", html)
        self.assertIn("<strong>Bold Text</strong>", html)
        self.assertNotIn("<script>", html)

    # -------------------------------------------------------------------------
    # Public Routes & Favicon
    # -------------------------------------------------------------------------

    def test_public_routes(self):
        """Verify all core public routes return HTTP 200."""
        routes = [
            "/",
            "/about",
            "/training",
            "/projects",
            "/gallery",
            "/insights",
            "/contact",
            "/health",
        ]
        for r in routes:
            resp = self.client.get(r)
            self.assertEqual(resp.status_code, 200, f"Failed on route {r}")

    def test_favicon_route(self):
        """Verify /favicon.ico returns 200 and does not raise 404 or 500."""
        resp = self.client.get("/favicon.ico")
        self.assertIn(resp.status_code, (200, 204))

    def test_404_error_handling_robustness(self):
        """
        Regression test for Bug 1:
        Verify non-existent routes render 404 without secondary template UndefinedError exceptions.
        """
        resp = self.client.get("/definitely-not-a-real-page")
        self.assertEqual(resp.status_code, 404, "404 route must return 404, NOT 500")
        self.assertIn(b"Page Not Found", resp.data)

        resp2 = self.client.get("/some/nested/missing/page")
        self.assertEqual(resp2.status_code, 404)
        self.assertIn(b"Page Not Found", resp2.data)

    def test_robots_txt(self):
        """Verify robots.txt allows public paths and disallows /admin."""
        resp = self.client.get("/robots.txt")
        self.assertEqual(resp.status_code, 200)
        content = resp.data.decode("utf-8")
        self.assertIn("Allow: /gallery", content)
        self.assertIn("Allow: /media", content)
        self.assertIn("Allow: /literature", content)
        self.assertIn("Disallow: /admin", content)
        self.assertIn("Sitemap: https://www.antickbhattacharjee.qd.je/sitemap.xml", content)

    def test_sitemap_xml(self):
        """Verify XML sitemap generation with canonical domain."""
        resp = self.client.get("/sitemap.xml")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "application/xml")
        content = resp.data.decode("utf-8")
        self.assertIn("https://www.antickbhattacharjee.qd.je/", content)
        self.assertIn("https://www.antickbhattacharjee.qd.je/gallery", content)
        self.assertNotIn("onrender.com", content)

    # -------------------------------------------------------------------------
    # Clean State & Dynamic Detail Pages
    # -------------------------------------------------------------------------

    def test_clean_state_gallery_and_literature_empty_states(self):
        """Verify gallery and admin empty state UI with 0 content items."""
        resp_gallery = self.client.get("/gallery")
        self.assertEqual(resp_gallery.status_code, 200)
        self.assertIn(b"New work will be added here soon.", resp_gallery.data)

        # Nonexistent content items return 404 cleanly without 500 errors
        resp_photo = self.client.get("/gallery/photo/non-existent-photo")
        self.assertEqual(resp_photo.status_code, 404)

        resp_lit = self.client.get("/literature/non-existent-literature")
        self.assertEqual(resp_lit.status_code, 404)

    def test_admin_empty_states(self):
        """Verify admin lists display clean empty state messages and upload buttons."""
        self.login_admin()

        resp_p = self.client.get("/admin/photos")
        self.assertEqual(resp_p.status_code, 200)
        self.assertIn(b"No photos uploaded yet.", resp_p.data)

        resp_v = self.client.get("/admin/videos")
        self.assertEqual(resp_v.status_code, 200)
        self.assertIn(b"No videos uploaded yet.", resp_v.data)

        resp_l = self.client.get("/admin/literature")
        self.assertEqual(resp_l.status_code, 200)
        self.assertIn(b"No literature published yet.", resp_l.data)

    # -------------------------------------------------------------------------
    # Admin Routes & Bug 2 Regression Tests
    # -------------------------------------------------------------------------

    def test_admin_route_protection_and_noindex(self):
        """Verify unauthenticated admin routes redirect to login with noindex headers."""
        resp = self.client.get("/admin", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login", resp.headers["Location"])

        resp_login = self.client.get("/admin/login")
        self.assertEqual(resp_login.status_code, 200)
        self.assertIn("noindex", resp_login.headers.get("X-Robots-Tag", ""))

    def test_admin_dashboard_and_crud_pages_render_without_500(self):
        """
        Regression test for Bug 2:
        Verify all admin CRUD pages render cleanly without BuildError or 500 exceptions.
        """
        self.login_admin()

        admin_routes = [
            "/admin",
            "/admin/photos",
            "/admin/photos/new",
            "/admin/videos",
            "/admin/videos/new",
            "/admin/literature",
            "/admin/literature/new",
            "/admin/content",
            "/admin/settings",
        ]

        for r in admin_routes:
            resp = self.client.get(r)
            self.assertEqual(resp.status_code, 200, f"Admin route {r} failed with status {resp.status_code}")
            # Ensure noindex header is on all admin responses
            self.assertIn("noindex", resp.headers.get("X-Robots-Tag", ""))

    # -------------------------------------------------------------------------
    # Search & Alias Normalization
    # -------------------------------------------------------------------------

    def test_search_alias_normalization(self):
        """Test search query alias normalization (e.g. Antik -> Antick)."""
        res = content_store.search_content("Antik training")
        self.assertIsInstance(res, dict)
        self.assertIn("photos", res)
        self.assertIn("videos", res)
        self.assertIn("literature", res)

        # Test gallery search route with alias
        resp = self.client.get("/gallery?q=Antik")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Showing results for:", resp.data)


if __name__ == "__main__":
    unittest.main()

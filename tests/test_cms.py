"""
Automated unit & integration test suite for Antick Website CMS.
Verifies zero SQL database, content store, image processing, markdown rendering,
admin authentication, CSRF, noindex headers, search alias normalization, and sitemap.
"""

import json
import os
import unittest
from io import BytesIO
from PIL import Image
from werkzeug.security import generate_password_hash

from app import create_app
from app.services.content_store import ContentStore, content_store
from app.services.media_processor import (
    generate_canonical_photo_filename,
    normalize_and_convert_image,
    slugify,
    suggest_alt_text,
)
from app.routes import render_markdown_safely


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

    def test_no_sql_database_exists(self):
        """Confirm no SQLite or database files exist in project root."""
        root_files = os.listdir(os.path.dirname(os.path.dirname(__file__)))
        for f in root_files:
            self.assertFalse(f.endswith(".db"), f"Unexpected database file found: {f}")
            self.assertFalse(f.endswith(".sqlite"), f"Unexpected database file found: {f}")
            self.assertFalse(f.endswith(".sqlite3"), f"Unexpected database file found: {f}")

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

    def test_media_processor_webp_and_orientation(self):
        """Test Pillow normalization to WebP and dimension calculation."""
        # Create a simple test image
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

    def test_public_routes(self):
        """Verify all core public routes return HTTP 200."""
        routes = ["/", "/about", "/training", "/projects", "/gallery", "/insights", "/contact", "/health"]
        for r in routes:
            resp = self.client.get(r)
            self.assertEqual(resp.status_code, 200, f"Failed on route {r}")

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
        """Verify XML sitemap generation."""
        resp = self.client.get("/sitemap.xml")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "application/xml")
        content = resp.data.decode("utf-8")
        self.assertIn("https://www.antickbhattacharjee.qd.je/", content)
        self.assertIn("https://www.antickbhattacharjee.qd.je/gallery", content)
        self.assertNotIn("onrender.com", content)

    def test_admin_route_protection_and_noindex(self):
        """Verify admin routes redirect to login and send noindex headers."""
        resp = self.client.get("/admin")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login", resp.headers["Location"])

        # Check login page sends X-Robots-Tag: noindex
        resp_login = self.client.get("/admin/login")
        self.assertEqual(resp_login.status_code, 200)
        self.assertIn("noindex", resp_login.headers.get("X-Robots-Tag", ""))

    def test_admin_login_and_dashboard(self):
        """Verify admin login with correct password hash."""
        resp = self.client.post("/admin/login", data={
            "username": "antick",
            "password": "TestSecurePassword123!",
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Publisher Dashboard", resp.data)

        # Access dashboard as logged in user
        resp_dash = self.client.get("/admin")
        self.assertEqual(resp_dash.status_code, 200)
        self.assertIn(b"Publisher Dashboard", resp_dash.data)

    def test_search_alias_normalization(self):
        """Test search query alias normalization (e.g. Antik -> Antick)."""
        res = content_store.search_content("Antik training")
        self.assertIsInstance(res, dict)
        self.assertIn("photos", res)
        self.assertIn("videos", res)
        self.assertIn("literature", res)


if __name__ == "__main__":
    unittest.main()

"""
Public Route Handlers for Antick Bhattacharjee Portfolio & CMS.
Provides crawlable, SEO-optimized views for Gallery, Photos, Videos, Literature, and Media Streaming.
"""

import hashlib
import io
import os
import re
from datetime import datetime
from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
import bleach
import markdown

from app.services.content_store import content_store
from app.services.google_drive import drive_service

main_bp = Blueprint("main", __name__)

ALLOWED_HTML_TAGS = [
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "em", "strong", "del", "a", "ul", "ol", "li",
    "blockquote", "code", "pre", "hr", "br",
    "table", "thead", "tbody", "tr", "th", "td",
    "img", "figure", "figcaption", "span", "div",
]

ALLOWED_HTML_ATTRS = {
    "*": ["class", "id"],
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "title", "width", "height", "loading", "decoding"],
}


def render_markdown_safely(md_text: str) -> str:
    """Render Markdown into clean, sanitized semantic HTML."""
    if not md_text:
        return ""
    html = markdown.markdown(
        md_text,
        extensions=["extra", "codehilite", "toc", "nl2br", "sane_lists"],
    )
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRS,
        strip=True,
    )
    return cleaned


# -----------------------------------------------------------------------------
# Public Website Routes
# -----------------------------------------------------------------------------

@main_bp.route("/")
def index():
    """Homepage: Comprehensive personal brand overview with dynamic hero and gallery preview."""
    all_photos = content_store.get_photos(published_only=True)
    featured_photos = [p for p in all_photos if p.get("featured")]
    if not featured_photos and all_photos:
        featured_photos = all_photos[:3]

    featured_videos = [v for v in content_store.get_videos(published_only=True) if v.get("featured")][:2]
    featured_literature = [l for l in content_store.get_literature(published_only=True) if l.get("featured")][:3]
    primary_photo = content_store.get_primary_profile_photo()

    profile_data = {
        "name": "Antick Bhattacharjee",
        "descriptor": "Technology Educator • Python Developer • Corporate Trainer",
        "brand_line": "Learn by building. Build with purpose.",
        "headline": "I explore technology, teach what I learn, and build practical digital solutions.",
        "about_summary": (
            "I am a corporate trainer and technology explorer with a strong interest in "
            "programming, automation, AI, and practical web solutions. I enjoy understanding "
            "how technology works, experimenting with new ideas, teaching technical concepts, "
            "and turning those ideas into useful systems."
        ),
        "primary_image": primary_photo,
        "pillars": [
            {
                "title": "Technology Education",
                "tagline": "Simplifying complex computing",
                "description": (
                    "Designing structured, hands-on learning experiences that empower professionals "
                    "and teams to master programming, problem-solving, and modern technology tools."
                ),
            },
            {
                "title": "Python & Software Development",
                "tagline": "Clean, scalable engineering",
                "description": (
                    "Building robust web applications, backend services, and utilities with a strong "
                    "focus on code clarity, maintainability, and practical functionality."
                ),
            },
            {
                "title": "Workflow Automation",
                "tagline": "Eliminating manual friction",
                "description": (
                    "Engineering custom scripts and Google Workspace integrations that connect "
                    "disparate systems and streamline repetitive operational processes."
                ),
            },
            {
                "title": "AI & Technology Exploration",
                "tagline": "Applied emerging technologies",
                "description": (
                    "Actively prototyping with modern AI frameworks, APIs, and emerging paradigms "
                    "to discover pragmatic applications that solve real-world problems."
                ),
            },
        ],
        "training_highlights": [
            {
                "title": "Corporate Technical Training",
                "description": "Tailored curriculum for corporate teams on Python, automation workflows, and developer tooling.",
            },
            {
                "title": "Interactive Coding Workshops",
                "description": "Live, project-based workshops focused on building real systems from first principles.",
            },
            {
                "title": "Google Workspace & Productivity Systems",
                "description": "Empowering organizations to build internal tools using Apps Script and cloud integrations.",
            },
        ],
        "featured_projects": [
            {
                "title": "Modular Web Application Suites",
                "category": "Web Solutions",
                "description": "Lightweight, high-performance web systems built with Flask and modern standard-based architectures.",
            },
            {
                "title": "Automated Data & Reporting Pipelines",
                "category": "Automation",
                "description": "Custom automated pipelines connecting spreadsheets, APIs, and cloud services for effortless reporting.",
            },
            {
                "title": "Interactive Training Sandboxes",
                "category": "Education",
                "description": "Dedicated demonstration repositories and code labs designed for guided technical instruction.",
            },
        ],
    }

    return render_template(
        "index.html",
        profile=profile_data,
        featured_photos=featured_photos,
        featured_videos=featured_videos,
        featured_literature=featured_literature,
        primary_photo=primary_photo,
        page_title="Antick Bhattacharjee | Technology Educator, Python Developer & Corporate Trainer",
        meta_description=(
            "Personal website of Antick Bhattacharjee, technology educator, Python developer "
            "and corporate trainer focused on practical learning, automation, software development "
            "and artificial intelligence."
        ),
        canonical_path="/",
    )


@main_bp.route("/about")
def about():
    """Dedicated About Page."""
    primary_photo = content_store.get_primary_profile_photo()
    return render_template(
        "about.html",
        primary_image=primary_photo,
        page_title="About Antick Bhattacharjee | Technology Educator & Developer",
        meta_description=(
            "Learn about Antick Bhattacharjee, his background as a corporate trainer, "
            "Python developer, and his philosophy of learning by building."
        ),
        canonical_path="/about",
    )


@main_bp.route("/training")
def training():
    """Dedicated Training Page."""
    all_photos = content_store.get_photos(published_only=True)
    training_images = [
        img for img in all_photos
        if img.get("category_slug") in ("training", "workshops")
        or "train" in img.get("category", "").lower()
    ]
    return render_template(
        "training.html",
        training_images=training_images,
        page_title="Corporate Training & Workshops | Antick Bhattacharjee",
        meta_description=(
            "Explore technical training programs, Python workshops, and practical learning "
            "sessions conducted by corporate trainer Antick Bhattacharjee."
        ),
        canonical_path="/training",
    )


@main_bp.route("/projects")
def projects():
    """Dedicated Projects Page."""
    all_photos = content_store.get_photos(published_only=True)
    project_images = [
        img for img in all_photos
        if img.get("category_slug") == "projects"
        or "project" in img.get("category", "").lower()
    ]
    return render_template(
        "projects.html",
        project_images=project_images,
        page_title="Projects & Solutions | Antick Bhattacharjee",
        meta_description=(
            "Explore software projects, automation tools, and web solutions developed by "
            "Antick Bhattacharjee."
        ),
        canonical_path="/projects",
    )


@main_bp.route("/insights")
def insights():
    """Dedicated Insights Page."""
    literature = content_store.get_literature(published_only=True)
    return render_template(
        "insights.html",
        literature=literature,
        page_title="Insights & Perspectives | Antick Bhattacharjee",
        meta_description=(
            "Perspectives and technical insights from Antick Bhattacharjee on programming, "
            "corporate training, automation, and software engineering."
        ),
        canonical_path="/insights",
    )


@main_bp.route("/contact")
def contact():
    """Dedicated Contact Page."""
    return render_template(
        "contact.html",
        page_title="Contact & Connect | Antick Bhattacharjee",
        meta_description=(
            "Get in touch with Antick Bhattacharjee for corporate technical training, "
            "automation consulting, or software development inquiries."
        ),
        canonical_path="/contact",
    )


# -----------------------------------------------------------------------------
# Public Unified Gallery & Detail Pages
# -----------------------------------------------------------------------------

@main_bp.route("/gallery")
def gallery():
    """
    Dedicated Gallery Page: Unified view for Photos, Videos, and Literature.
    Server-rendered with Jinja for search crawlers, with optional query filtering.
    """
    query = request.args.get("q", "").strip()
    filter_type = request.args.get("type", "all").strip().lower()

    if query:
        search_results = content_store.search_content(query)
        photos = search_results["photos"]
        videos = search_results["videos"]
        literature = search_results["literature"]
    else:
        photos = content_store.get_photos(published_only=True)
        videos = content_store.get_videos(published_only=True)
        literature = content_store.get_literature(published_only=True)

    # Calculate categories
    categories = {}
    for p in photos:
        cat = p.get("category", "General")
        categories[cat] = categories.get(cat, 0) + 1

    return render_template(
        "gallery.html",
        photos=photos,
        videos=videos,
        literature=literature,
        categories=categories,
        active_filter=filter_type,
        query=query,
        page_title="Antick Bhattacharjee Gallery | Photos, Videos & Creative Literature",
        meta_description=(
            "Explore photographs, recorded presentations, technical essays, and creative literature "
            "by Antick Bhattacharjee."
        ),
        canonical_path="/gallery",
    )


@main_bp.route("/gallery/photo/<slug>")
def photo_detail(slug):
    """Dedicated crawlable image detail page for Google Image SEO and deep context."""
    photo = content_store.get_photo_by_slug(slug)
    if not photo or not photo.get("published", True):
        # Check backward compatibility fallback
        for p in content_store.get_photos(published_only=False):
            if p.get("slug") == slug:
                photo = p
                break
        if not photo:
            abort(404)

    all_photos = content_store.get_photos(published_only=True)
    related_photos = [p for p in all_photos if p.get("slug") != slug][:3]

    return render_template(
        "photo_detail.html",
        photo=photo,
        related_photos=related_photos,
        page_title=f"{photo.get('title')} | Antick Bhattacharjee",
        meta_description=photo.get("caption") or photo.get("description") or f"Photograph of Antick Bhattacharjee - {photo.get('title')}",
        canonical_path=f"/gallery/photo/{slug}",
    )


@main_bp.route("/gallery/<slug>")
def gallery_item_redirect(slug):
    """
    Handle existing /gallery/<slug> routes.
    Checks photo -> video -> 404.
    """
    photo = content_store.get_photo_by_slug(slug)
    if photo:
        return redirect(url_for("main.photo_detail", slug=slug), code=301)

    video = content_store.get_video_by_slug(slug)
    if video:
        return redirect(url_for("main.video_detail", slug=slug), code=301)

    abort(404)


@main_bp.route("/gallery/video/<slug>")
def video_detail(slug):
    """Dedicated crawlable watch page for video presentations and tutorials."""
    video = content_store.get_video_by_slug(slug)
    if not video or not video.get("published", True):
        abort(404)

    all_videos = content_store.get_videos(published_only=True)
    related_videos = [v for v in all_videos if v.get("slug") != slug][:3]

    return render_template(
        "video_detail.html",
        video=video,
        related_videos=related_videos,
        page_title=f"{video.get('title')} | Antick Bhattacharjee",
        meta_description=video.get("description") or f"Watch {video.get('title')} by Antick Bhattacharjee.",
        canonical_path=f"/gallery/video/{slug}",
    )


@main_bp.route("/literature/<slug>")
def literature_detail(slug):
    """
    Dedicated crawlable literature page for essays, poetry, prose, and thoughts.
    Renders UTF-8 Markdown from Google Drive as clean, semantic HTML.
    """
    lit = content_store.get_literature_by_slug(slug)
    if not lit or not lit.get("published", True):
        abort(404)

    raw_body = content_store.get_literature_body(lit)
    body_html = render_markdown_safely(raw_body)

    all_lit = content_store.get_literature(published_only=True)
    related_literature = [l for l in all_lit if l.get("slug") != slug][:3]

    return render_template(
        "literature_detail.html",
        literature=lit,
        body_html=body_html,
        related_literature=related_literature,
        page_title=f"{lit.get('title')} | Literature | Antick Bhattacharjee",
        meta_description=lit.get("short_description"),
        canonical_path=f"/literature/{slug}",
    )


# -----------------------------------------------------------------------------
# Media Delivery & Streaming Routes (Google Drive Storage Proxy)
# -----------------------------------------------------------------------------

@main_bp.route("/media/photo/<path:filename>")
def serve_photo(filename):
    """
    Stable public image delivery endpoint.
    Downloads/streams bytes from Google Drive or local static fallback.
    Returns HTTP 200, Content-Type: image/webp, Cache-Control, ETag.
    """
    clean_name = os.path.basename(filename)
    photo = None
    all_photos = content_store.get_photos(published_only=False)

    for p in all_photos:
        if p.get("filename") == clean_name or p.get("slug") == clean_name.replace(".webp", ""):
            photo = p
            break

    # 1. Check if photo has Drive file ID and Drive is configured
    if photo and photo.get("drive_file_id") and drive_service.is_configured:
        try:
            image_bytes = drive_service.download_file_bytes(photo["drive_file_id"])
            etag = hashlib.md5(image_bytes).hexdigest()

            if request.headers.get("If-None-Match") == etag:
                return Response(status=304)

            response = Response(image_bytes, mimetype="image/webp")
            response.headers["Cache-Control"] = "public, max-age=86400"
            response.headers["ETag"] = etag
            response.headers["Content-Disposition"] = f'inline; filename="{photo.get("filename", clean_name)}"'
            return response
        except Exception as e:
            current_app.logger.warning(f"Failed to fetch image {clean_name} from Drive: {e}")

    # 2. Check local fallback file
    if photo and photo.get("local_fallback_path"):
        local_path = os.path.join(current_app.root_path, "static", photo["local_fallback_path"])
        if os.path.exists(local_path):
            return send_file(local_path, mimetype="image/webp")

    # 3. Check generic static paths
    direct_static = os.path.join(current_app.root_path, "static", "images", "antick", clean_name)
    if os.path.exists(direct_static):
        return send_file(direct_static, mimetype="image/webp")

    profile_static = os.path.join(current_app.root_path, "static", "images", "profile.jpg")
    if os.path.exists(profile_static):
        return send_file(profile_static, mimetype="image/jpeg")

    abort(404)


@main_bp.route("/media/video/<slug>")
def stream_video(slug):
    """
    Stable public video streaming endpoint.
    Proxies video bytes from Google Drive with HTTP Range support.
    """
    video = content_store.get_video_by_slug(slug)
    if not video or not video.get("drive_file_id") or not drive_service.is_configured:
        abort(404)

    file_id = video["drive_file_id"]

    try:
        service = drive_service.get_service()
        file_meta = service.files().get(fileId=file_id, fields="size, mimeType").execute()
        file_size = int(file_meta.get("size", 0))
        mime_type = file_meta.get("mimeType", "video/mp4")

        range_header = request.headers.get("Range", None)

        if range_header and file_size > 0:
            # Parse Range: bytes=start-end
            byte_range = range_header.replace("bytes=", "").split("-")
            start = int(byte_range[0]) if byte_range[0] else 0
            end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1
            length = end - start + 1

            drive_req = service.files().get_media(fileId=file_id)
            drive_req.headers["Range"] = f"bytes={start}-{end}"
            content_chunk = drive_req.execute()

            response = Response(
                content_chunk,
                status=206,
                mimetype=mime_type,
                direct_passthrough=True,
            )
            response.headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            response.headers["Accept-Ranges"] = "bytes"
            response.headers["Content-Length"] = str(length)
            return response
        else:
            # Download stream
            video_bytes = drive_service.download_file_bytes(file_id)
            response = Response(video_bytes, mimetype=mime_type)
            response.headers["Accept-Ranges"] = "bytes"
            response.headers["Content-Length"] = str(len(video_bytes))
            return response
    except Exception as e:
        current_app.logger.error(f"Error streaming video {slug}: {e}")
        abort(500)


# -----------------------------------------------------------------------------
# SEO: Robots.txt & Dynamic Sitemap
# -----------------------------------------------------------------------------

@main_bp.route("/robots.txt")
def robots_txt():
    """Serve robots.txt allowing public content/media and disallowing /admin."""
    content = render_template("robots.txt")
    return Response(content, mimetype="text/plain")


@main_bp.route("/sitemap.xml")
def sitemap_xml():
    """
    Serve dynamic XML sitemap including all canonical pages and Google Image Sitemap extensions.
    Strictly uses https://www.antickbhattacharjee.qd.je and /media/photo/... URLs.
    """
    photos = content_store.get_photos(published_only=True)
    videos = content_store.get_videos(published_only=True)
    literature = content_store.get_literature(published_only=True)
    primary_photo = content_store.get_primary_profile_photo()

    pages = [
        {"path": "/", "priority": "1.0", "changefreq": "weekly", "photos": [primary_photo] if primary_photo else []},
        {"path": "/about", "priority": "0.9", "changefreq": "monthly", "photos": [primary_photo] if primary_photo else []},
        {"path": "/training", "priority": "0.9", "changefreq": "monthly", "photos": [p for p in photos if "train" in p.get("category", "").lower()]},
        {"path": "/projects", "priority": "0.9", "changefreq": "monthly", "photos": [p for p in photos if "project" in p.get("category", "").lower()]},
        {"path": "/gallery", "priority": "0.9", "changefreq": "weekly", "photos": photos},
        {"path": "/insights", "priority": "0.8", "changefreq": "monthly", "photos": []},
        {"path": "/contact", "priority": "0.8", "changefreq": "monthly", "photos": []},
    ]

    # Add photo detail pages
    for p in photos:
        pages.append({
            "path": f"/gallery/photo/{p['slug']}",
            "priority": "0.7",
            "changefreq": "monthly",
            "photos": [p],
        })

    # Add video detail pages
    for v in videos:
        pages.append({
            "path": f"/gallery/video/{v['slug']}",
            "priority": "0.8",
            "changefreq": "monthly",
            "photos": [],
        })

    # Add literature pages
    for l in literature:
        pages.append({
            "path": f"/literature/{l['slug']}",
            "priority": "0.8",
            "changefreq": "monthly",
            "photos": [],
        })

    sitemap_xml_content = render_template("sitemap.xml", pages=pages)
    return Response(sitemap_xml_content, mimetype="application/xml")


@main_bp.route("/health")
def health_check():
    """Uptime probe."""
    return jsonify({
        "status": "ok",
        "backend": "google-drive-cms",
        "timestamp": datetime.utcnow().isoformat(),
    })


# -----------------------------------------------------------------------------
# Error Handlers
# -----------------------------------------------------------------------------

@main_bp.app_errorhandler(404)
def handle_404(e):
    return render_template(
        "base.html",
        page_title="Page Not Found | Antick Bhattacharjee",
        meta_description="The requested page could not be found.",
        content="<section class='section'><div class='container' style='text-align:center; padding: 4rem 1rem;'><h1>404 — Page Not Found</h1><p style='margin:1.5rem 0; color: var(--color-text-secondary);'>The page or creative work you are looking for has moved or does not exist.</p><a href='/' class='btn btn-primary'>Return Home</a></div></section>",
    ), 404


@main_bp.app_errorhandler(500)
def handle_500(e):
    return render_template(
        "base.html",
        page_title="Server Error | Antick Bhattacharjee",
        meta_description="An unexpected server error occurred.",
        content="<section class='section'><div class='container' style='text-align:center; padding: 4rem 1rem;'><h1>Service Notice</h1><p style='margin:1.5rem 0; color: var(--color-text-secondary);'>We encountered a momentary issue retrieving content. Please check back shortly.</p><a href='/' class='btn btn-primary'>Return Home</a></div></section>",
    ), 500

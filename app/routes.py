from flask import Blueprint, Response, abort, jsonify, render_template, request
from app.gallery_data import (
    get_all_images,
    get_categories,
    get_featured_images,
    get_image_by_slug,
    get_primary_profile_image,
)

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Homepage: Comprehensive personal brand overview."""
    featured_images = get_featured_images()
    primary_image = get_primary_profile_image()

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
        "primary_image": primary_image,
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
        "insights_preview": [
            {
                "title": "The Value of First-Principles Learning in Programming",
                "date": "2026",
                "excerpt": "Why understanding foundational computing and architecture beats chasing fleeting framework trends every single time.",
            },
            {
                "title": "Pragmatic Automation: Where to Start in Your Workflow",
                "date": "2026",
                "excerpt": "A systematic approach to identifying repetitive tasks and building dependable scripts that save hours every week.",
            },
        ],
    }

    return render_template(
        "index.html",
        profile=profile_data,
        featured_images=featured_images,
        primary_image=primary_image,
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
    """Dedicated About Page: Background, philosophy, and focus areas."""
    primary_image = get_primary_profile_image()
    return render_template(
        "about.html",
        primary_image=primary_image,
        page_title="About Antick Bhattacharjee | Technology Educator & Developer",
        meta_description=(
            "Learn about Antick Bhattacharjee, his background as a corporate trainer, "
            "Python developer, and his philosophy of learning by building."
        ),
        canonical_path="/about",
    )


@main_bp.route("/training")
def training():
    """Dedicated Training Page: Workshops, corporate offerings, and pedagogy."""
    training_images = [img for img in get_all_images() if img.get("category_slug") in ("training", "workshops")]
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
    """Dedicated Projects Page: Web solutions, automation pipelines, and tools."""
    project_images = [img for img in get_all_images() if img.get("category_slug") == "projects"]
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


@main_bp.route("/gallery")
def gallery():
    """Dedicated Gallery Page: Comprehensive image gallery with contextual groups."""
    images = get_all_images()
    categories = get_categories()
    return render_template(
        "gallery.html",
        images=images,
        categories=categories,
        page_title="Antick Bhattacharjee Gallery | Training, Technology & Professional Photos",
        meta_description=(
            "Explore photographs of Antick Bhattacharjee from technical training sessions, "
            "workshops, technology projects and professional activities."
        ),
        canonical_path="/gallery",
    )


@main_bp.route("/gallery/<slug>")
def image_detail(slug):
    """Dedicated crawlable image detail page for Google Image SEO and deep context."""
    image = get_image_by_slug(slug)
    if not image:
        abort(404)

    all_images = get_all_images()
    related_images = [img for img in all_images if img["slug"] != slug][:3]

    return render_template(
        "image_detail.html",
        image=image,
        related_images=related_images,
        page_title=f"{image['title']} | Antick Bhattacharjee",
        meta_description=image["caption"],
        canonical_path=f"/gallery/{slug}",
    )


@main_bp.route("/insights")
def insights():
    """Dedicated Insights Page: Perspectives on technology, education, and development."""
    return render_template(
        "insights.html",
        page_title="Insights & Perspectives | Antick Bhattacharjee",
        meta_description=(
            "Perspectives and technical insights from Antick Bhattacharjee on programming, "
            "corporate training, automation, and software engineering."
        ),
        canonical_path="/insights",
    )


@main_bp.route("/contact")
def contact():
    """Dedicated Contact Page: Professional inquiries, social channels, and location."""
    return render_template(
        "contact.html",
        page_title="Contact & Connect | Antick Bhattacharjee",
        meta_description=(
            "Get in touch with Antick Bhattacharjee for corporate technical training, "
            "automation consulting, or software development inquiries."
        ),
        canonical_path="/contact",
    )


@main_bp.route("/robots.txt")
def robots_txt():
    """Serve robots.txt for search engines."""
    content = render_template("robots.txt")
    return Response(content, mimetype="text/plain")


@main_bp.route("/sitemap.xml")
def sitemap_xml():
    """Serve valid XML sitemap including Google Image Sitemap extensions."""
    images = get_all_images()
    pages = [
        {"path": "/", "priority": "1.0", "changefreq": "weekly", "images": [get_primary_profile_image()]},
        {"path": "/about", "priority": "0.9", "changefreq": "monthly", "images": [get_primary_profile_image()]},
        {"path": "/training", "priority": "0.9", "changefreq": "monthly", "images": [img for img in images if img.get("category_slug") == "training"]},
        {"path": "/projects", "priority": "0.9", "changefreq": "monthly", "images": [img for img in images if img.get("category_slug") == "projects"]},
        {"path": "/gallery", "priority": "0.9", "changefreq": "weekly", "images": images},
        {"path": "/insights", "priority": "0.8", "changefreq": "monthly", "images": []},
        {"path": "/contact", "priority": "0.8", "changefreq": "monthly", "images": []},
    ]

    # Include dedicated image detail pages in sitemap
    for img in images:
        pages.append({
            "path": f"/gallery/{img['slug']}",
            "priority": "0.7",
            "changefreq": "monthly",
            "images": [img],
        })

    sitemap_xml_content = render_template("sitemap.xml", pages=pages)
    return Response(sitemap_xml_content, mimetype="application/xml")


@main_bp.route("/health")
def health_check():
    """Health check endpoint for monitoring and uptime probes."""
    return jsonify({"status": "ok"})

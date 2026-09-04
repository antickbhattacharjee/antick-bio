"""
Gallery data repository for Antick Bhattacharjee's portfolio.
Provides structured metadata for image SEO, contextual rendering,
Schema.org ImageObject generation, and XML image sitemaps.
"""

GALLERY_IMAGES = [
    {
        "slug": "antick-bhattacharjee-profile",
        "filename": "antick-bhattacharjee-profile.webp",
        "relative_path": "images/antick/profile/antick-bhattacharjee-profile.webp",
        "category": "Professional Portraits",
        "category_slug": "portraits",
        "title": "Portrait of Antick Bhattacharjee",
        "alt": "Portrait of Antick Bhattacharjee, technology educator, Python developer, and corporate trainer",
        "caption": "Antick Bhattacharjee — Technology Educator, Python Developer, and Corporate Trainer.",
        "description": (
            "Official professional portrait of Antick Bhattacharjee. Antick works actively in "
            "corporate technical training, Python application development, and practical workflow automation."
        ),
        "context": "Professional Profile & Identity",
        "date": "2026",
        "width": 800,
        "height": 800,
        "featured": True,
        "is_primary_profile": True,
    },
    {
        "slug": "antick-bhattacharjee-corporate-training-session",
        "filename": "antick-bhattacharjee-corporate-training-session.webp",
        "relative_path": "images/antick/training/antick-bhattacharjee-corporate-training-session.webp",
        "category": "Training Sessions",
        "category_slug": "training",
        "title": "Corporate Technical Training Session",
        "alt": "Antick Bhattacharjee conducting a corporate technical training session",
        "caption": "Antick Bhattacharjee leading a technical corporate training session on programming and practical systems.",
        "description": (
            "A snapshot from a corporate training session led by Antick Bhattacharjee, focusing on practical "
            "problem-solving, coding workflows, and effective implementation methodologies."
        ),
        "context": "Corporate Training & Professional Workshops",
        "date": "2026",
        "width": 1200,
        "height": 800,
        "featured": True,
        "is_primary_profile": False,
    },
    {
        "slug": "antick-bhattacharjee-python-training-session",
        "filename": "antick-bhattacharjee-python-training-session.webp",
        "relative_path": "images/antick/training/antick-bhattacharjee-python-training-session.webp",
        "category": "Training Sessions",
        "category_slug": "training",
        "title": "Hands-on Python Training Workshop",
        "alt": "Antick Bhattacharjee guiding participants during a hands-on Python training session",
        "caption": "Antick Bhattacharjee mentoring participants during an interactive Python programming workshop.",
        "description": (
            "Antick Bhattacharjee facilitating an interactive Python development workshop, demonstrating live code, "
            "debugging techniques, and structured software design principles."
        ),
        "context": "Hands-on Python Education & Mentorship",
        "date": "2026",
        "width": 1200,
        "height": 800,
        "featured": True,
        "is_primary_profile": False,
    },
    {
        "slug": "antick-bhattacharjee-technical-workshop",
        "filename": "antick-bhattacharjee-technical-workshop.webp",
        "relative_path": "images/antick/training/antick-bhattacharjee-technical-workshop.webp",
        "category": "Workshops",
        "category_slug": "workshops",
        "title": "Classroom Technology Workshop",
        "alt": "Antick Bhattacharjee speaking during a classroom technology workshop",
        "caption": "Antick Bhattacharjee breaking down practical software architectures in a classroom workshop setting.",
        "description": (
            "During a dedicated technical workshop, Antick Bhattacharjee explains core computing concepts, "
            "automation strategies, and real-world system integrations to learners."
        ),
        "context": "Technical Workshops & Classroom Learning",
        "date": "2026",
        "width": 1200,
        "height": 800,
        "featured": True,
        "is_primary_profile": False,
    },
    {
        "slug": "antick-bhattacharjee-speaking-at-training-session",
        "filename": "antick-bhattacharjee-speaking-at-training-session.webp",
        "relative_path": "images/antick/events/antick-bhattacharjee-speaking-at-training-session.webp",
        "category": "Speaking & Presentations",
        "category_slug": "speaking",
        "title": "Speaking on Modern Technology Solutions",
        "alt": "Antick Bhattacharjee speaking at a technical presentation on software and automation",
        "caption": "Antick Bhattacharjee presenting practical approaches to workflow automation and digital tooling.",
        "description": (
            "Antick Bhattacharjee addressing attendees during a technical talk covering automation paradigms, "
            "AI-assisted development, and pragmatic engineering practices."
        ),
        "context": "Presentations & Technology Discussions",
        "date": "2026",
        "width": 1200,
        "height": 800,
        "featured": True,
        "is_primary_profile": False,
    },
    {
        "slug": "antick-bhattacharjee-working-on-web-project",
        "filename": "antick-bhattacharjee-working-on-web-project.webp",
        "relative_path": "images/antick/projects/antick-bhattacharjee-working-on-web-project.webp",
        "category": "Technology Projects",
        "category_slug": "projects",
        "title": "Developing Web Solutions & Automation Tools",
        "alt": "Antick Bhattacharjee working on a web development and automation project",
        "caption": "Antick Bhattacharjee engineering web applications and automation workflows in the development workspace.",
        "description": (
            "A glimpse into the development process where Antick Bhattacharjee builds, tests, and refines custom "
            "web solutions and automated scripts for modern digital environments."
        ),
        "context": "Software Engineering & Project Prototyping",
        "date": "2026",
        "width": 1200,
        "height": 800,
        "featured": True,
        "is_primary_profile": False,
    },
]


def get_all_images():
    """Return all gallery images."""
    return GALLERY_IMAGES


def get_featured_images():
    """Return images marked as featured for homepage display."""
    return [img for img in GALLERY_IMAGES if img.get("featured")]


def get_image_by_slug(slug):
    """Lookup a gallery image record by its unique URL slug."""
    for img in GALLERY_IMAGES:
        if img.get("slug") == slug:
            return img
    return None


def get_primary_profile_image():
    """Return the primary identity portrait image record."""
    for img in GALLERY_IMAGES:
        if img.get("is_primary_profile"):
            return img
    return GALLERY_IMAGES[0] if GALLERY_IMAGES else None


def get_categories():
    """Return unique categories with count and metadata."""
    categories = {}
    for img in GALLERY_IMAGES:
        cat_name = img.get("category", "General")
        cat_slug = img.get("category_slug", "general")
        if cat_slug not in categories:
            categories[cat_slug] = {
                "name": cat_name,
                "slug": cat_slug,
                "count": 1,
            }
        else:
            categories[cat_slug]["count"] += 1
    return list(categories.values())

import os
from datetime import datetime
from flask import Flask
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()


def create_app(test_config=None):
    """Application factory for Antick Bhattacharjee Personal Website & CMS."""
    app = Flask(__name__, instance_relative_config=True)

    # Base configuration
    max_upload_mb = int(os.environ.get("MAX_VIDEO_UPLOAD_MB", 150))
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-key-antick-portfolio-change-in-prod"),
        CANONICAL_HOST="https://www.antickbhattacharjee.qd.je",
        MAX_CONTENT_LENGTH=max_upload_mb * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=(os.environ.get("FLASK_ENV") == "production"),
        WTF_CSRF_TIME_LIMIT=None,
    )

    if test_config:
        app.config.from_mapping(test_config)

    # Initialize extensions
    csrf.init_app(app)

    # Context processors to inject common template variables across all views
    @app.context_processor
    def inject_global_vars():
        from app.services.content_store import content_store
        primary_photo = content_store.get_primary_profile_photo()
        
        # Determine primary profile image URL
        if primary_photo:
            primary_image_url = f"/media/photo/{primary_photo.get('filename')}"
            primary_image_alt = primary_photo.get("alt_text") or "Portrait of Antick Bhattacharjee"
        else:
            primary_image_url = "/static/images/profile.jpg"
            primary_image_alt = "Portrait of Antick Bhattacharjee"

        canonical_host = app.config.get("CANONICAL_HOST", "https://www.antickbhattacharjee.qd.je")
        
        # Safely resolve request path for global canonical & nav highlighting
        try:
            from flask import request
            current_path = request.path if request else "/"
        except Exception:
            current_path = "/"

        return {
            "current_year": datetime.now().year,
            "canonical_host": canonical_host,
            "canonical_path": current_path,
            "canonical_url": f"{canonical_host}{current_path}",
            "author_name": "Antick Bhattacharjee",
            "brand_line": "Learn by building. Build with purpose.",
            "primary_descriptor": "Technology Educator • Python Developer • Corporate Trainer",
            "site_title_default": "Antick Bhattacharjee | Technology Educator, Python Developer & Corporate Trainer",
            "page_title": "Antick Bhattacharjee | Technology Educator, Python Developer & Corporate Trainer",
            "meta_description": "Personal website of Antick Bhattacharjee, technology educator, Python developer and corporate trainer focused on practical learning, automation, software development and artificial intelligence.",
            "primary_profile_image_url": f"{canonical_host}{primary_image_url}",
            "primary_profile_image_relative": primary_image_url,
            "primary_profile_image_alt": primary_image_alt,
            "social_links": {
                "linkedin": "https://www.linkedin.com/in/antickbhattacharjee/",
                "instagram": "https://www.instagram.com/antickbhattacharjee/",
                "facebook": "https://www.facebook.com/imantick",
                "github": "https://github.com/antickbhattacharjee",
            },
            "location": "West Bengal, India",
        }

    # Register Blueprints
    from app.routes import main_bp
    from app.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    return app

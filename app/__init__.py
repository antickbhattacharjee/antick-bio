import os
from datetime import datetime
from flask import Flask


def create_app(test_config=None):
    """Application factory for the Flask personal website."""
    app = Flask(__name__, instance_relative_config=True)

    # Base configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-key-antick-portfolio-change-in-prod"),
        CANONICAL_HOST="https://www.antickbhattacharjee.qd.je",
    )

    if test_config:
        app.config.from_mapping(test_config)

    # Context processors to inject common template variables across all views
    @app.context_processor
    def inject_global_vars():
        return {
            "current_year": datetime.now().year,
            "canonical_host": app.config.get("CANONICAL_HOST", "https://www.antickbhattacharjee.qd.je"),
            "author_name": "Antick Bhattacharjee",
            "brand_line": "Learn by building. Build with purpose.",
            "primary_descriptor": "Technology Educator • Python Developer • Corporate Trainer",
            "site_title_default": "Antick Bhattacharjee | Technology Educator, Python Developer & Corporate Trainer",
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
    app.register_blueprint(main_bp)

    return app

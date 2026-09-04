import os
from datetime import datetime
from flask import Flask


def create_app(test_config=None):
    """Application factory for the Flask portfolio website."""
    app = Flask(__name__, instance_relative_config=True)

    # Base configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-key-antick-portfolio-change-in-prod"),
    )

    if test_config:
        app.config.from_mapping(test_config)

    # Context processors to inject common template variables
    @app.context_processor
    def inject_global_vars():
        return {
            "current_year": datetime.now().year,
            "site_title": "Antick Bhattacharjee | Trainer, Explorer & Builder",
            "author_name": "Antick Bhattacharjee",
        }

    # Register Blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app

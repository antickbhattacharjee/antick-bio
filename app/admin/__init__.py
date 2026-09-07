"""
Admin Blueprint initialization with authentication decorators and security headers.
"""

from functools import wraps
from flask import Blueprint, redirect, session, url_for, request

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def login_required(f):
    """Decorator to require single-owner admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.after_request
def add_admin_security_headers(response):
    """Ensure search engines never index any admin route."""
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


# Import routes to register handlers
from app.admin import routes  # noqa: E402, F401

from flask import Blueprint, jsonify, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Render the single-page personal portfolio website."""
    profile_data = {
        "name": "Antick Bhattacharjee",
        "tagline": "Trainer. Explorer. Builder.",
        "headline": "I explore technology, teach what I learn, and build practical digital solutions.",
        "about": (
            "I am a corporate trainer and technology explorer with a strong interest in "
            "programming, automation, AI, and practical web solutions. I enjoy understanding "
            "how technology works, experimenting with new ideas, teaching technical concepts, "
            "and turning those ideas into useful systems."
        ),
        "pillars": [
            {
                "title": "Corporate Training",
                "icon": "chalkboard",
                "description": (
                    "Delivering structured technical sessions and workshops that translate "
                    "complex concepts into clear, actionable skills for teams and professionals."
                ),
            },
            {
                "title": "Web Solutions",
                "icon": "browser",
                "description": (
                    "Crafting functional, accessible, and responsive web applications and digital "
                    "interfaces tailored to solve specific everyday operational problems."
                ),
            },
            {
                "title": "Automation",
                "icon": "gears",
                "description": (
                    "Designing intelligent workflows, scripts, and Google Workspace integrations "
                    "to eliminate repetitive manual tasks and enhance operational efficiency."
                ),
            },
            {
                "title": "Technology Exploration",
                "icon": "cpu",
                "description": (
                    "Actively prototyping and experimenting with emerging technologies, modern "
                    "programming languages, system architectures, and AI-assisted tooling."
                ),
            },
        ],
        "contact": {
            "email": "YOUR_EMAIL",
            "linkedin": "YOUR_LINKEDIN_URL",
            "github": "YOUR_GITHUB_URL",
            "location": "West Bengal, India",
        },
    }
    return render_template("index.html", profile=profile_data)


@main_bp.route("/health")
def health_check():
    """Health check endpoint for monitoring, load balancers, and uptime probes."""
    return jsonify({"status": "ok"})

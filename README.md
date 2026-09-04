# Antick Bhattacharjee - Personal Profile Website

A clean, modular, and responsive personal profile and portfolio website for **Antick Bhattacharjee** (Corporate Trainer, Technology Explorer, and Automation & Web Solution Builder), built using **Python, Flask, Jinja2, HTML5, and Vanilla CSS3**.

---

## 1. Project Purpose

This repository represents **Phase 1** of a scalable personal platform. The goal is to provide a clean, professional, and accessible web foundation that:
- Establishes a personal brand presence at `antickbhattacharjee.qd.je`.
- Presents core focus areas: Corporate Training, Web Solutions, Workflow Automation, and Technology Exploration.
- Provides direct contact links and monitoring endpoints.
- Maintains a modular Flask application factory architecture designed to seamlessly scale into future features (blog, project showcase, dynamic contact forms, API integrations, Google Workspace automations, etc.).

---

## 2. Project Structure

```text
personal-profile/
│
├── run.py                 # Local development entry point
├── wsgi.py                # Production WSGI entry point (for Gunicorn)
├── requirements.txt       # Minimal Python dependencies
├── .gitignore             # Python / OS ignore rules
├── .env.example           # Environment variable template
├── README.md              # Project documentation & setup instructions
│
└── app/
    ├── __init__.py        # Flask application factory (create_app)
    ├── routes.py          # Application routes and blueprint definitions
    │
    ├── templates/
    │   ├── base.html      # Base HTML5 layout, metadata, navigation & footer
    │   └── index.html     # Single-page sections (Hero, About, Work, Contact)
    │
    └── static/
        ├── css/
        │   └── style.css  # Custom CSS design system (tokens, layout, responsive)
        │
        ├── js/
        │   └── main.js    # Minimal vanilla JavaScript (navigation, image fallback)
        │
        └── images/
            └── .gitkeep   # Image assets directory (place profile.jpg here)
```

---

## 3. Getting Started & Local Development

### Prerequisites
- Python 3.9+ installed on your system.

### Step 1: Clone or Navigate to the Directory
```bash
cd d:/Projects/bio
```

### Step 2: Create a Virtual Environment
- **On Windows (PowerShell / Command Prompt):**
  ```powershell
  python -m venv venv
  venv\Scripts\activate
  ```
- **On macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### Step 5: Run the Development Server
```bash
python run.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## 4. Production Deployment

The project includes a production WSGI entry point (`wsgi.py`) ready for WSGI HTTP servers like **Gunicorn**:

```bash
gunicorn wsgi:app --bind 0.0.0.0:8000 --workers 4
```

### Health Check Endpoint
A dedicated monitoring endpoint is available at `/health` for uptime checks, Docker healthchecks, and reverse proxies:
```bash
curl http://127.0.0.1:5000/health
# Response: {"status": "ok"}
```

---

## 5. Customization & Personal Information

### Modifying Personal Details
All content is cleanly decoupled:
1. **Profile Data & Contact Info**: Open [`app/routes.py`](file:///d:/Projects/bio/app/routes.py) to update:
   - `email` (replace `YOUR_EMAIL` with your actual email)
   - `linkedin` (replace `YOUR_LINKEDIN_URL` with your LinkedIn URL)
   - `github` (replace `YOUR_GITHUB_URL` with your GitHub URL)
   - `location` (currently set to `West Bengal, India`)
2. **Text / Copy**: The hero headline, about paragraphs, and focus card descriptions can be updated in `app/routes.py` or directly customized in [`app/templates/index.html`](file:///d:/Projects/bio/app/templates/index.html).
3. **Theme & Colors**: All visual styles use CSS Custom Properties in [`app/static/css/style.css`](file:///d:/Projects/bio/app/static/css/style.css) under `:root`.

---

## 6. Profile Image

- To add your photo, place your portrait image in:
  ```
  app/static/images/profile.jpg
  ```
- If no image is provided, the website automatically and elegantly falls back to a clean monogram avatar badge (`AB`) with zero visual glitch or broken image icons.

---

## 7. Future Expansion Roadmap

The architecture is built with Flask Blueprints and modular templates to easily accommodate future phases:

- [ ] **Projects Portfolio**: Dedicated project cards with case studies and live demos.
- [ ] **Training Catalog**: Course syllabi, workshop details, and scheduling inquiries.
- [ ] **Interactive Contact Form**: Backend form processing, CSRF protection, and email notifications (e.g., SendGrid / SMTP).
- [ ] **Technical Blog / Articles**: Markdown or database-backed technical writing.
- [ ] **Google Workspace Integrations**: Automated booking and contact synchronization.
- [ ] **AI Experiment Showcases**: Embedded interactive demonstrations and API utilities.
- [ ] **Database & Admin Dashboard**: SQLite/PostgreSQL with Flask-SQLAlchemy for dynamic content updates.

---

## 8. License

&copy; Antick Bhattacharjee. All rights reserved.

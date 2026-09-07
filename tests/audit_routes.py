"""
Route and template endpoint audit tool.
Verifies every url_for in every Jinja template against Flask's registered url_map.
"""

import glob
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app

app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
registered_endpoints = set(app.view_functions.keys())
print(f"Registered endpoints in Flask url_map ({len(registered_endpoints)}):")
for ep in sorted(registered_endpoints):
    print(f"  - {ep}")

url_for_pattern = re.compile(r"url_for\(\s*['\"]([^'\"]+)['\"]")
errors = []

for template_path in PROJECT_ROOT.glob("app/templates/**/*.html"):
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    for line_no, line in enumerate(content.splitlines(), start=1):
        for match in url_for_pattern.finditer(line):
            ep = match.group(1)
            if ep not in registered_endpoints and ep != "static":
                errors.append((str(template_path.relative_to(PROJECT_ROOT)), line_no, ep))

if errors:
    print("\n[ERROR] Found invalid endpoint references in templates:")
    for file_path, line_no, ep in errors:
        print(f"  {file_path}:{line_no} -> '{ep}' does not exist!")
    sys.exit(1)
else:
    print("\n[SUCCESS] Every url_for in every template matches a valid registered endpoint!")

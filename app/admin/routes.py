"""
Admin CMS route handlers for managing photos, videos, literature, settings, and authentication.
"""

import os
from datetime import datetime
from flask import (
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.admin import admin_bp, login_required
from app.admin.forms import (
    ChangePasswordForm,
    LiteratureForm,
    LoginForm,
    PhotoForm,
    VideoForm,
)
from app.services.content_store import content_store
from app.services.google_drive import drive_service
from app.services.media_processor import (
    generate_canonical_photo_filename,
    normalize_and_convert_image,
    slugify,
    suggest_alt_text,
)


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        admin_user = os.environ.get("ADMIN_USERNAME", "antick")
        admin_hash = os.environ.get("ADMIN_PASSWORD_HASH", "")

        if form.username.data.strip() == admin_user and admin_hash and check_password_hash(admin_hash, form.password.data):
            session.clear()
            session["admin_logged_in"] = True
            session["admin_user"] = admin_user
            flash("Welcome back, Antick!", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("admin.dashboard"))
        else:
            flash("Invalid administrator credentials. Please try again.", "danger")

    return render_template("admin/login.html", form=form)


@admin_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("admin.login"))


@admin_bp.route("", strict_slashes=False)
@admin_bp.route("/", strict_slashes=False)
@login_required
def dashboard():
    manifest = content_store.load_manifest()
    photos = manifest.get("photos", [])
    videos = manifest.get("videos", [])
    literature = manifest.get("literature", [])

    stats = {
        "total_photos": len(photos),
        "published_photos": sum(1 for p in photos if p.get("published", True)),
        "total_videos": len(videos),
        "published_videos": sum(1 for v in videos if v.get("published", True)),
        "total_literature": len(literature),
        "published_literature": sum(1 for l in literature if l.get("published", True)),
        "drive_configured": drive_service.is_configured,
    }

    recent_photos = sorted(photos, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
    recent_videos = sorted(videos, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
    recent_literature = sorted(literature, key=lambda x: x.get("created_at", ""), reverse=True)[:5]

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_photos=recent_photos,
        recent_videos=recent_videos,
        recent_literature=recent_literature,
    )


# -----------------------------------------------------------------------------
# Photos CRUD
# -----------------------------------------------------------------------------

@admin_bp.route("/photos")
@login_required
def photos_list():
    photos = content_store.get_photos(published_only=False)
    return render_template("admin/photos_list.html", photos=photos)


@admin_bp.route("/photos/new", methods=["GET", "POST"])
@login_required
def photo_new():
    form = PhotoForm()
    if form.validate_on_submit():
        file = form.photo_file.data
        if not file:
            flash("Please select an image file to upload.", "danger")
            return render_template("admin/photo_form.html", form=form, title="Upload New Photo")

        # Read & normalize image
        raw_bytes = file.read()
        processed_webp, width, height, mime_type = normalize_and_convert_image(raw_bytes)

        # Generate canonical filename & slug
        all_photos = content_store.get_photos(published_only=False)
        next_index = len(all_photos) + 1
        filename = generate_canonical_photo_filename(next_index)

        title = form.title.data.strip()
        slug = slugify(title)
        # Avoid slug collisions
        existing_slug = content_store.get_photo_by_slug(slug)
        if existing_slug:
            slug = f"{slug}-{next_index}"

        # Upload to Google Drive
        drive_file_id = ""
        if drive_service.is_configured:
            photos_folder_id = os.environ.get("GOOGLE_DRIVE_PHOTOS_FOLDER_ID")
            upload_res = drive_service.upload_file(
                name=filename,
                data=processed_webp,
                mime_type="image/webp",
                parent_id=photos_folder_id,
                description=form.caption.data or title,
            )
            drive_file_id = upload_res["id"]

        alt_text = form.alt_text.data.strip() if form.alt_text.data else suggest_alt_text(title, form.category.data)
        tags = [t.strip() for t in form.tags.data.split(",") if t.strip()]

        photo_data = {
            "slug": slug,
            "filename": filename,
            "drive_file_id": drive_file_id,
            "mime_type": mime_type,
            "width": width,
            "height": height,
            "title": title,
            "description": form.description.data.strip() if form.description.data else "",
            "caption": form.caption.data.strip() if form.caption.data else "",
            "alt_text": alt_text,
            "category": form.category.data.strip() if form.category.data else "General",
            "category_slug": slugify(form.category.data.strip()) if form.category.data else "general",
            "tags": tags,
            "date": form.date.data.strip() if form.date.data else "2026",
            "location": form.location.data.strip() if form.location.data else "West Bengal, India",
            "featured": form.featured.data,
            "primary_profile": form.primary_profile.data,
            "published": form.published.data,
        }

        content_store.save_photo(photo_data)
        flash(f"Photo '{title}' uploaded and published successfully!", "success")
        return redirect(url_for("admin.photos_list"))

    return render_template("admin/photo_form.html", form=form, title="Upload New Photo")


@admin_bp.route("/photos/<photo_id>/edit", methods=["GET", "POST"])
@login_required
def photo_edit(photo_id):
    photo = content_store.get_photo_by_id(photo_id)
    if not photo:
        flash("Photo not found.", "danger")
        return redirect(url_for("admin.photos_list"))

    form = PhotoForm(data=photo)
    if request.method == "GET":
        form.tags.data = ", ".join(photo.get("tags", []))

    if form.validate_on_submit():
        # Check if replacement file uploaded
        if form.photo_file.data:
            raw_bytes = form.photo_file.data.read()
            processed_webp, width, height, mime_type = normalize_and_convert_image(raw_bytes)
            photo["width"] = width
            photo["height"] = height
            if photo.get("drive_file_id") and drive_service.is_configured:
                drive_service.update_file_content(
                    file_id=photo["drive_file_id"],
                    data=processed_webp,
                    mime_type="image/webp",
                )
            elif drive_service.is_configured:
                photos_folder_id = os.environ.get("GOOGLE_DRIVE_PHOTOS_FOLDER_ID")
                upload_res = drive_service.upload_file(
                    name=photo.get("filename", "antick-bhattacharjee-photo.webp"),
                    data=processed_webp,
                    mime_type="image/webp",
                    parent_id=photos_folder_id,
                )
                photo["drive_file_id"] = upload_res["id"]

        title = form.title.data.strip()
        photo["title"] = title
        photo["caption"] = form.caption.data.strip() if form.caption.data else ""
        photo["alt_text"] = form.alt_text.data.strip() if form.alt_text.data else suggest_alt_text(title, form.category.data)
        photo["description"] = form.description.data.strip() if form.description.data else ""
        photo["category"] = form.category.data.strip() if form.category.data else "General"
        photo["category_slug"] = slugify(form.category.data.strip()) if form.category.data else "general"
        photo["tags"] = [t.strip() for t in form.tags.data.split(",") if t.strip()]
        photo["date"] = form.date.data.strip() if form.date.data else "2026"
        photo["location"] = form.location.data.strip() if form.location.data else "West Bengal, India"
        photo["featured"] = form.featured.data
        photo["primary_profile"] = form.primary_profile.data
        photo["published"] = form.published.data

        content_store.save_photo(photo)
        flash(f"Photo '{title}' updated successfully.", "success")
        return redirect(url_for("admin.photos_list"))

    return render_template("admin/photo_form.html", form=form, title=f"Edit: {photo.get('title')}", photo=photo)


@admin_bp.route("/photos/<photo_id>/delete", methods=["POST"])
@login_required
def photo_delete(photo_id):
    success = content_store.delete_photo(photo_id, delete_drive_file=True)
    if success:
        flash("Photo deleted successfully.", "info")
    else:
        flash("Could not find photo to delete.", "warning")
    return redirect(url_for("admin.photos_list"))


# -----------------------------------------------------------------------------
# Videos CRUD
# -----------------------------------------------------------------------------

@admin_bp.route("/videos")
@login_required
def videos_list():
    videos = content_store.get_videos(published_only=False)
    return render_template("admin/videos_list.html", videos=videos)


@admin_bp.route("/videos/new", methods=["GET", "POST"])
@login_required
def video_new():
    form = VideoForm()
    if form.validate_on_submit():
        video_file = form.video_file.data
        poster_file = form.poster_file.data

        title = form.title.data.strip()
        slug = slugify(title)
        existing_video = content_store.get_video_by_slug(slug)
        if existing_video:
            slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

        drive_file_id = ""
        poster_drive_file_id = ""

        if drive_service.is_configured:
            videos_folder_id = os.environ.get("GOOGLE_DRIVE_VIDEOS_FOLDER_ID")
            if video_file:
                v_res = drive_service.upload_file(
                    name=f"{slug}.mp4",
                    data=video_file.read(),
                    mime_type="video/mp4",
                    parent_id=videos_folder_id,
                    description=title,
                )
                drive_file_id = v_res["id"]

            if poster_file:
                p_webp, _, _, _ = normalize_and_convert_image(poster_file.read())
                p_res = drive_service.upload_file(
                    name=f"{slug}-poster.webp",
                    data=p_webp,
                    mime_type="image/webp",
                    parent_id=videos_folder_id,
                )
                poster_drive_file_id = p_res["id"]

        tags = [t.strip() for t in form.tags.data.split(",") if t.strip()]
        video_data = {
            "slug": slug,
            "filename": f"{slug}.mp4",
            "drive_file_id": drive_file_id,
            "poster_drive_file_id": poster_drive_file_id,
            "mime_type": "video/mp4",
            "title": title,
            "description": form.description.data.strip() if form.description.data else "",
            "category": form.category.data.strip() if form.category.data else "Presentations",
            "category_slug": slugify(form.category.data.strip()) if form.category.data else "presentations",
            "tags": tags,
            "date": form.date.data.strip() if form.date.data else "2026",
            "transcript": form.transcript.data.strip() if form.transcript.data else "",
            "featured": form.featured.data,
            "published": form.published.data,
        }

        content_store.save_video(video_data)
        flash(f"Video '{title}' saved successfully!", "success")
        return redirect(url_for("admin.videos_list"))

    return render_template("admin/video_form.html", form=form, title="Add New Video")


@admin_bp.route("/videos/<video_id>/edit", methods=["GET", "POST"])
@login_required
def video_edit(video_id):
    video = content_store.get_video_by_id(video_id)
    if not video:
        flash("Video not found.", "danger")
        return redirect(url_for("admin.videos_list"))

    form = VideoForm(data=video)
    if request.method == "GET":
        form.tags.data = ", ".join(video.get("tags", []))

    if form.validate_on_submit():
        if form.video_file.data and drive_service.is_configured:
            videos_folder_id = os.environ.get("GOOGLE_DRIVE_VIDEOS_FOLDER_ID")
            v_res = drive_service.upload_file(
                name=f"{video['slug']}.mp4",
                data=form.video_file.data.read(),
                mime_type="video/mp4",
                parent_id=videos_folder_id,
            )
            video["drive_file_id"] = v_res["id"]

        if form.poster_file.data and drive_service.is_configured:
            videos_folder_id = os.environ.get("GOOGLE_DRIVE_VIDEOS_FOLDER_ID")
            p_webp, _, _, _ = normalize_and_convert_image(form.poster_file.data.read())
            p_res = drive_service.upload_file(
                name=f"{video['slug']}-poster.webp",
                data=p_webp,
                mime_type="image/webp",
                parent_id=videos_folder_id,
            )
            video["poster_drive_file_id"] = p_res["id"]

        title = form.title.data.strip()
        video["title"] = title
        video["description"] = form.description.data.strip() if form.description.data else ""
        video["category"] = form.category.data.strip() if form.category.data else "Presentations"
        video["category_slug"] = slugify(form.category.data.strip()) if form.category.data else "presentations"
        video["tags"] = [t.strip() for t in form.tags.data.split(",") if t.strip()]
        video["date"] = form.date.data.strip() if form.date.data else "2026"
        video["transcript"] = form.transcript.data.strip() if form.transcript.data else ""
        video["featured"] = form.featured.data
        video["published"] = form.published.data

        content_store.save_video(video)
        flash(f"Video '{title}' updated successfully.", "success")
        return redirect(url_for("admin.videos_list"))

    return render_template("admin/video_form.html", form=form, title=f"Edit: {video.get('title')}", video=video)


@admin_bp.route("/videos/<video_id>/delete", methods=["POST"])
@login_required
def video_delete(video_id):
    content_store.delete_video(video_id, delete_drive_file=True)
    flash("Video deleted successfully.", "info")
    return redirect(url_for("admin.videos_list"))


# -----------------------------------------------------------------------------
# Literature CRUD
# -----------------------------------------------------------------------------

@admin_bp.route("/literature")
@login_required
def literature_list():
    literature = content_store.get_literature(published_only=False)
    return render_template("admin/literature_list.html", literature=literature)


@admin_bp.route("/literature/new", methods=["GET", "POST"])
@login_required
def literature_new():
    form = LiteratureForm()
    if form.validate_on_submit():
        title = form.title.data.strip()
        slug = slugify(title)
        existing = content_store.get_literature_by_slug(slug)
        if existing:
            slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

        tags = [t.strip() for t in form.tags.data.split(",") if t.strip()]
        lit_data = {
            "slug": slug,
            "title": title,
            "content_type": form.content_type.data,
            "short_description": form.short_description.data.strip(),
            "body": form.body.data,  # Local fallback
            "tags": tags,
            "publication_date": form.publication_date.data.strip() if form.publication_date.data else "2026-01-01",
            "featured": form.featured.data,
            "published": form.published.data,
        }

        content_store.save_literature(lit_data, body_markdown=form.body.data)
        flash(f"Literature entry '{title}' published successfully!", "success")
        return redirect(url_for("admin.literature_list"))

    return render_template("admin/literature_form.html", form=form, title="New Literature Piece")


@admin_bp.route("/literature/<lit_id>/edit", methods=["GET", "POST"])
@login_required
def literature_edit(lit_id):
    lit = content_store.get_literature_by_id(lit_id)
    if not lit:
        flash("Literature piece not found.", "danger")
        return redirect(url_for("admin.literature_list"))

    form = LiteratureForm(data=lit)
    if request.method == "GET":
        form.tags.data = ", ".join(lit.get("tags", []))
        form.body.data = content_store.get_literature_body(lit)

    if form.validate_on_submit():
        title = form.title.data.strip()
        lit["title"] = title
        lit["content_type"] = form.content_type.data
        lit["short_description"] = form.short_description.data.strip()
        lit["body"] = form.body.data
        lit["tags"] = [t.strip() for t in form.tags.data.split(",") if t.strip()]
        lit["publication_date"] = form.publication_date.data.strip() if form.publication_date.data else "2026-01-01"
        lit["featured"] = form.featured.data
        lit["published"] = form.published.data

        content_store.save_literature(lit, body_markdown=form.body.data)
        flash(f"Literature '{title}' updated successfully.", "success")
        return redirect(url_for("admin.literature_list"))

    return render_template("admin/literature_form.html", form=form, title=f"Edit: {lit.get('title')}", literature=lit)


@admin_bp.route("/literature/<lit_id>/delete", methods=["POST"])
@login_required
def literature_delete(lit_id):
    content_store.delete_literature(lit_id, delete_drive_file=True)
    flash("Literature entry deleted successfully.", "info")
    return redirect(url_for("admin.literature_list"))


# -----------------------------------------------------------------------------
# Raw Manifest & Backups
# -----------------------------------------------------------------------------

@admin_bp.route("/content")
@login_required
def content_view():
    manifest = content_store.load_manifest(force_refresh=True)
    return render_template("admin/content_view.html", manifest=manifest)


# -----------------------------------------------------------------------------
# Settings & Password Management
# -----------------------------------------------------------------------------

@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    form = ChangePasswordForm()
    admin_user = os.environ.get("ADMIN_USERNAME", "antick")
    current_hash = os.environ.get("ADMIN_PASSWORD_HASH", "")

    if form.validate_on_submit():
        if not check_password_hash(current_hash, form.current_password.data):
            flash("Current password verification failed. Please try again.", "danger")
            return render_template("admin/settings.html", form=form, admin_user=admin_user)

        new_hash = generate_password_hash(form.new_password.data)
        os.environ["ADMIN_PASSWORD_HASH"] = new_hash

        # Update local .env safely if present
        env_path = current_app.root_path + "/../.env"
        try:
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                with open(env_path, "w", encoding="utf-8") as f:
                    hash_replaced = False
                    for line in lines:
                        if line.startswith("ADMIN_PASSWORD_HASH="):
                            f.write(f"ADMIN_PASSWORD_HASH={new_hash}\n")
                            hash_replaced = True
                        else:
                            f.write(line)
                    if not hash_replaced:
                        f.write(f"ADMIN_PASSWORD_HASH={new_hash}\n")
        except Exception as e:
            current_app.logger.warning(f"Could not write new password hash to local .env: {e}")

        flash("Admin password updated successfully! Please note the Render instructions below if running in production.", "success")
        return render_template("admin/settings.html", form=form, admin_user=admin_user, new_hash=new_hash)

    return render_template("admin/settings.html", form=form, admin_user=admin_user)

"""
Gallery data helper module for Antick Bhattacharjee's website.
Delegates to the Google Drive content_store service.
"""

GALLERY_IMAGES = []


def get_all_images():
    """Return all published photos from content store."""
    from app.services.content_store import content_store
    return content_store.get_photos(published_only=True)


def get_featured_images():
    """Return featured photos from content store."""
    from app.services.content_store import content_store
    photos = content_store.get_photos(published_only=True)
    return [p for p in photos if p.get("featured")]


def get_image_by_slug(slug):
    """Lookup a photo record by its slug."""
    from app.services.content_store import content_store
    return content_store.get_photo_by_slug(slug)


def get_primary_profile_image():
    """Return the primary identity portrait image record if one has been designated."""
    from app.services.content_store import content_store
    return content_store.get_primary_profile_photo()


def get_categories():
    """Return unique categories with count and metadata."""
    images = get_all_images()
    categories = {}
    for img in images:
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

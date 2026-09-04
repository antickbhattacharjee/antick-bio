/**
 * Antick Bhattacharjee - Personal Portfolio & Gallery
 * Lightweight Vanilla JavaScript for Accessible Navigation, Gallery Filters & Lightbox
 */

document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------------------
    // 1. Mobile Navigation Drawer Toggle
    // -------------------------------------------------------------------------
    const navToggle = document.getElementById('nav-toggle');
    const primaryNav = document.getElementById('primary-nav');
    const navLinks = document.querySelectorAll('.nav-link');

    if (navToggle && primaryNav) {
        navToggle.addEventListener('click', () => {
            const isOpen = primaryNav.classList.toggle('is-open');
            navToggle.setAttribute('aria-expanded', String(isOpen));
        });

        // Close mobile drawer upon navigating
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (primaryNav.classList.contains('is-open')) {
                    primaryNav.classList.remove('is-open');
                    navToggle.setAttribute('aria-expanded', 'false');
                }
            });
        });

        // Close when clicking outside header
        document.addEventListener('click', (e) => {
            if (primaryNav.classList.contains('is-open') && !primaryNav.contains(e.target) && !navToggle.contains(e.target)) {
                primaryNav.classList.remove('is-open');
                navToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // -------------------------------------------------------------------------
    // 2. Gallery Category Filtering (on /gallery page)
    // -------------------------------------------------------------------------
    const filterButtons = document.querySelectorAll('.gallery-filter-btn');
    const galleryCards = document.querySelectorAll('.gallery-card[data-category]');

    if (filterButtons.length > 0 && galleryCards.length > 0) {
        filterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetFilter = btn.getAttribute('data-filter');

                // Update active state
                filterButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // Filter cards
                galleryCards.forEach(card => {
                    const cardCategory = card.getAttribute('data-category');
                    if (targetFilter === 'all' || cardCategory === targetFilter) {
                        card.style.display = 'flex';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        });
    }

    // -------------------------------------------------------------------------
    // 3. Accessible Gallery Lightbox Modal
    // -------------------------------------------------------------------------
    const lightboxModal = document.getElementById('lightbox-modal');
    const lightboxBackdrop = document.getElementById('lightbox-backdrop');
    const lightboxClose = document.getElementById('lightbox-close');
    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxTitle = document.getElementById('lightbox-title');
    const lightboxCaption = document.getElementById('lightbox-caption');
    const lightboxDetailLink = document.getElementById('lightbox-detail-link');
    const lightboxPrev = document.getElementById('lightbox-prev');
    const lightboxNext = document.getElementById('lightbox-next');

    let activeGalleryCards = [];
    let currentImageIndex = -1;
    let lastActiveElement = null;

    function getVisibleGalleryCards() {
        return Array.from(document.querySelectorAll('.gallery-card[data-full-src]')).filter(
            card => card.style.display !== 'none'
        );
    }

    function openLightbox(index, triggerEl) {
        if (!lightboxModal) return;
        activeGalleryCards = getVisibleGalleryCards();
        if (index < 0 || index >= activeGalleryCards.length) return;

        currentImageIndex = index;
        lastActiveElement = triggerEl || document.activeElement;

        updateLightboxContent();

        lightboxModal.classList.add('is-open');
        lightboxModal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';

        if (lightboxClose) lightboxClose.focus();
    }

    function closeLightbox() {
        if (!lightboxModal) return;
        lightboxModal.classList.remove('is-open');
        lightboxModal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';

        if (lastActiveElement && typeof lastActiveElement.focus === 'function') {
            lastActiveElement.focus();
        }
    }

    function updateLightboxContent() {
        if (currentImageIndex < 0 || currentImageIndex >= activeGalleryCards.length) return;
        const card = activeGalleryCards[currentImageIndex];
        const fullSrc = card.getAttribute('data-full-src');
        const title = card.getAttribute('data-title') || '';
        const caption = card.getAttribute('data-caption') || '';
        const detailUrl = card.getAttribute('data-detail-url') || '#';

        if (lightboxImg) {
            lightboxImg.src = fullSrc;
            lightboxImg.alt = title;
        }
        if (lightboxTitle) lightboxTitle.textContent = title;
        if (lightboxCaption) lightboxCaption.textContent = caption;
        if (lightboxDetailLink) {
            lightboxDetailLink.href = detailUrl;
            lightboxDetailLink.style.display = detailUrl && detailUrl !== '#' ? 'inline-block' : 'none';
        }
    }

    function showPrevImage() {
        if (activeGalleryCards.length <= 1) return;
        currentImageIndex = (currentImageIndex - 1 + activeGalleryCards.length) % activeGalleryCards.length;
        updateLightboxContent();
    }

    function showNextImage() {
        if (activeGalleryCards.length <= 1) return;
        currentImageIndex = (currentImageIndex + 1) % activeGalleryCards.length;
        updateLightboxContent();
    }

    // Attach click listeners to gallery cards and zoom buttons
    const allGalleryCards = document.querySelectorAll('.gallery-card[data-full-src]');
    allGalleryCards.forEach(card => {
        const zoomBtn = card.querySelector('.gallery-zoom-btn');
        const imgWrapper = card.querySelector('.gallery-image-wrapper');

        const triggerHandler = (e) => {
            // Prevent opening lightbox if user clicked direct detail link inside caption
            if (e.target.closest('a')) return;
            const visibleCards = getVisibleGalleryCards();
            const idx = visibleCards.indexOf(card);
            if (idx !== -1) {
                openLightbox(idx, zoomBtn || card);
            }
        };

        if (zoomBtn) {
            zoomBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const visibleCards = getVisibleGalleryCards();
                const idx = visibleCards.indexOf(card);
                if (idx !== -1) openLightbox(idx, zoomBtn);
            });
        }

        if (imgWrapper) {
            imgWrapper.addEventListener('click', triggerHandler);
        }
    });

    if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
    if (lightboxBackdrop) lightboxBackdrop.addEventListener('click', closeLightbox);
    if (lightboxPrev) lightboxPrev.addEventListener('click', showPrevImage);
    if (lightboxNext) lightboxNext.addEventListener('click', showNextImage);

    // Keyboard navigation for Lightbox
    document.addEventListener('keydown', (e) => {
        if (!lightboxModal || !lightboxModal.classList.contains('is-open')) return;

        if (e.key === 'Escape') {
            closeLightbox();
        } else if (e.key === 'ArrowLeft') {
            showPrevImage();
        } else if (e.key === 'ArrowRight') {
            showNextImage();
        }
    });

    // -------------------------------------------------------------------------
    // 4. Fallback Handling for Profile Image
    // -------------------------------------------------------------------------
    const heroImg = document.getElementById('hero-portrait-img');
    const avatarFallback = document.getElementById('avatar-fallback');

    if (heroImg && avatarFallback) {
        heroImg.addEventListener('error', () => {
            heroImg.style.display = 'none';
            avatarFallback.style.display = 'flex';
        });
    }
});

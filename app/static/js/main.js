/**
 * Antick Bhattacharjee - Personal Portfolio
 * Minimal Vanilla JavaScript for Navigation & Image Fallback
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Navigation Menu Toggle
    const navToggle = document.getElementById('nav-toggle');
    const primaryNav = document.getElementById('primary-nav');
    const navLinks = document.querySelectorAll('.nav-link');

    if (navToggle && primaryNav) {
        navToggle.addEventListener('click', () => {
            const isOpen = primaryNav.classList.toggle('is-open');
            navToggle.setAttribute('aria-expanded', String(isOpen));
        });

        // Close mobile menu on nav link click
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (primaryNav.classList.contains('is-open')) {
                    primaryNav.classList.remove('is-open');
                    navToggle.setAttribute('aria-expanded', 'false');
                }
            });
        });
    }

    // 2. Active Section Highlighting using IntersectionObserver
    const sections = document.querySelectorAll('section[id]');
    
    if ('IntersectionObserver' in window && sections.length > 0) {
        const observerOptions = {
            root: null,
            rootMargin: '-30% 0px -60% 0px',
            threshold: 0
        };

        const observerCallback = (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const id = entry.target.getAttribute('id');
                    navLinks.forEach(link => {
                        const href = link.getAttribute('href');
                        if (href === `#${id}`) {
                            link.classList.add('active');
                        } else {
                            link.classList.remove('active');
                        }
                    });
                }
            });
        };

        const sectionObserver = new IntersectionObserver(observerCallback, observerOptions);
        sections.forEach(section => sectionObserver.observe(section));
    }

    // 3. Profile Image Fallback Detection
    const profileImg = document.getElementById('profile-img');
    const avatarPlaceholder = document.getElementById('avatar-placeholder');

    if (profileImg && avatarPlaceholder) {
        // If the profile image loads successfully, swap out placeholder
        profileImg.addEventListener('load', () => {
            if (profileImg.naturalWidth > 0 && profileImg.naturalHeight > 0) {
                profileImg.classList.add('is-loaded');
                avatarPlaceholder.style.display = 'none';
            }
        });

        // If it fails or is not found, keep the fallback placeholder active
        profileImg.addEventListener('error', () => {
            profileImg.style.display = 'none';
            avatarPlaceholder.style.display = 'flex';
        });

        // Handle cached image already complete
        if (profileImg.complete) {
            if (profileImg.naturalWidth > 0) {
                profileImg.classList.add('is-loaded');
                avatarPlaceholder.style.display = 'none';
            } else {
                profileImg.style.display = 'none';
                avatarPlaceholder.style.display = 'flex';
            }
        }
    }
});

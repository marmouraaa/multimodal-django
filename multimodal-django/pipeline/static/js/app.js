/* ============================================
   MULTIMODAL AI PIPELINE - MODERN INTERACTIONS
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initScrollReveal();
    initConfidenceRings();
    initCounterAnimations();
    addBlobElement();
});

/* ============================================
   DARK / LIGHT MODE TOGGLE
   ============================================ */
function initThemeToggle() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    const html = document.documentElement;
    const icon = toggle.querySelector('i');

    const saved = localStorage.getItem('theme');
    if (saved) {
        html.setAttribute('data-theme', saved);
        updateThemeIcon(icon, saved);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        html.setAttribute('data-theme', 'dark');
        updateThemeIcon(icon, 'dark');
    }

    toggle.addEventListener('click', () => {
        const current = html.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        updateThemeIcon(icon, next);
    });
}

function updateThemeIcon(icon, theme) {
    if (!icon) return;
    icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
}

/* ============================================
   SCROLL REVEAL ANIMATIONS
   ============================================ */
function initScrollReveal() {
    const elements = document.querySelectorAll('.reveal');
    if (!elements.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -40px 0px'
    });

    elements.forEach(el => observer.observe(el));
}

/* ============================================
   CONFIDENCE RING ANIMATION
   ============================================ */
function initConfidenceRings() {
    const rings = document.querySelectorAll('.confidence-ring .ring-fill');
    rings.forEach(ring => {
        const percent = parseFloat(ring.dataset.percent) || 0;
        const radius = parseFloat(ring.getAttribute('r')) || 52;
        const circumference = 2 * Math.PI * radius;

        ring.style.strokeDasharray = circumference;
        ring.style.strokeDashoffset = circumference;

        setTimeout(() => {
            const offset = circumference - (percent / 100) * circumference;
            ring.style.strokeDashoffset = offset;
        }, 300);
    });
}

/* ============================================
   COUNTER ANIMATIONS
   ============================================ */
function initCounterAnimations() {
    const counters = document.querySelectorAll('.counter-animate');
    if (!counters.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(el => observer.observe(el));
}

function animateCounter(el) {
    const target = parseFloat(el.dataset.target) || 0;
    const suffix = el.dataset.suffix || '';
    const duration = 1200;
    const start = performance.now();

    function update(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = eased * target;

        if (Number.isInteger(target)) {
            el.textContent = Math.round(current) + suffix;
        } else {
            el.textContent = current.toFixed(2) + suffix;
        }

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

/* ============================================
   EXTRA BACKGROUND BLOB
   ============================================ */
function addBlobElement() {
    if (document.querySelector('.blob-3')) return;
    const blob = document.createElement('div');
    blob.className = 'blob-3';
    blob.setAttribute('aria-hidden', 'true');
    document.body.appendChild(blob);
}

/* ============================================
   DRAG & DROP — FIX DOUBLE FILE DIALOG
   
   Root cause: the drop-zone div has a click listener
   that calls fileInput.click(). But clicks on child
   elements (the submit button, labels, etc.) bubble
   up to the drop-zone and fire the dialog a second time.
   
   Fix:
   1. Use a _dialogOpen flag to block re-entrant calls.
   2. Only trigger on clicks that actually hit the zone
      background (not buttons or the invisible input).
   3. Guard with a 500ms cooldown after dialog opens.
   ============================================ */
function initDragDrop(dropZoneId, fileInputId, callbacks) {
    const dropZone = document.getElementById(dropZoneId);
    const fileInput = document.getElementById(fileInputId);
    if (!dropZone || !fileInput) return;

    let dialogOpen = false;

    function openDialog() {
        if (dialogOpen) return;
        dialogOpen = true;
        fileInput.click();
        // Reset flag after a short delay (dialog close fires no reliable event)
        setTimeout(() => { dialogOpen = false; }, 500);
    }

    // Click on drop-zone background → open dialog
    // Exclude clicks that originate from: button, input, a, label
    dropZone.addEventListener('click', (e) => {
        const tag = e.target.tagName.toUpperCase();
        const EXCLUDED = ['BUTTON', 'INPUT', 'A', 'LABEL'];
        if (EXCLUDED.includes(tag)) return;
        // Also exclude if click came from inside a button
        if (e.target.closest('button') || e.target.closest('a')) return;
        openDialog();
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            if (callbacks && callbacks.onFile) {
                callbacks.onFile(e.dataTransfer.files[0]);
            }
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            if (callbacks && callbacks.onFile) {
                callbacks.onFile(e.target.files[0]);
            }
        }
    });
}

/* ============================================
   UTILITY: Format file size
   ============================================ */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' octets';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' Ko';
    return (bytes / 1048576).toFixed(1) + ' Mo';
}

/* ============================================
   CLIENT-SIDE SEARCH FILTER
   ============================================ */
function initSearchFilter(inputId, cardsSelector) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.addEventListener('input', () => {
        const query = input.value.toLowerCase().trim();
        const cards = document.querySelectorAll(cardsSelector);

        cards.forEach(card => {
            const text = card.textContent.toLowerCase();
            const parent = card.closest('.col-md-6') || card.parentElement;
            if (parent) {
                parent.style.display = text.includes(query) ? '' : 'none';
            }
        });
    });
}
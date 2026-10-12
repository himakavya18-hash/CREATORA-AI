/**
 * Creatora AI - Client-Side Interactive Engine
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Tooltips initialization
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(el => new bootstrap.Tooltip(el));

    // 2. Auto-dismiss flash alerts after 6 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(alert => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        });
    }, 6000);

    // 3. Theme Toggle (Dark / Light)
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    if (themeToggleBtn) {
        const currentTheme = localStorage.getItem('creatora_theme') || 'dark';
        document.documentElement.setAttribute('data-bs-theme', currentTheme);
        updateThemeIcon(themeToggleBtn, currentTheme);

        themeToggleBtn.addEventListener('click', () => {
            const activeTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('creatora_theme', newTheme);
            updateThemeIcon(themeToggleBtn, newTheme);
        });
    }

    function updateThemeIcon(btn, theme) {
        const icon = btn.querySelector('i');
        if (icon) {
            if (theme === 'light') {
                icon.className = 'bi bi-moon-stars-fill text-primary';
            } else {
                icon.className = 'bi bi-sun-fill text-warning';
            }
        }
    }

    // 4. AJAX Save Creator Bookmark
    document.querySelectorAll('.btn-save-creator').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const creatorId = btn.dataset.creatorId;
            const csrfToken = getCsrfToken();
            try {
                const res = await fetch(`/brand/save-creator/${creatorId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    }
                });
                const data = await res.json();
                if (data.success) {
                    const icon = btn.querySelector('i');
                    if (data.is_saved) {
                        btn.classList.add('text-danger');
                        if (icon) icon.className = 'bi bi-heart-fill';
                        btn.title = 'Saved to shortlist';
                    } else {
                        btn.classList.remove('text-danger');
                        if (icon) icon.className = 'bi bi-heart';
                        btn.title = 'Save creator';
                    }
                }
            } catch (err) {
                console.error('Error toggling creator save:', err);
            }
        });
    });

    // 5. AJAX Save Campaign Bookmark
    document.querySelectorAll('.btn-save-brief').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const briefId = btn.dataset.briefId;
            const csrfToken = getCsrfToken();
            try {
                const res = await fetch(`/briefs/${briefId}/save`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    }
                });
                const data = await res.json();
                if (data.success) {
                    const icon = btn.querySelector('i');
                    if (data.is_saved) {
                        btn.classList.add('text-warning');
                        if (icon) icon.className = 'bi bi-bookmark-fill';
                    } else {
                        btn.classList.remove('text-warning');
                        if (icon) icon.className = 'bi bi-bookmark';
                    }
                }
            } catch (err) {
                console.error('Error toggling campaign bookmark:', err);
            }
        });
    });

    // Helper: get CSRF token from meta or hidden input
    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) return meta.getAttribute('content');
        const input = document.querySelector('input[name="csrf_token"]');
        return input ? input.value : '';
    }
});

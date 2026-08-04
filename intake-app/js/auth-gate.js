// Temporary client-side login gate for Upstar testing only.
// This is not secure and must be replaced with real server-side or hosting-level auth before any sensitive production use.
(function() {
    'use strict';

    const CONFIG = window.WATSON_AUTH_CONFIG || {};
    const STORAGE_KEY = 'upstar_temp_access_v1';
    const TEST_USERNAME = 'upstarmhs';
    const TEST_PASSWORD = 'Up5t@r2026!';

    function hasAccess() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (!saved) return false;
            const parsed = JSON.parse(saved);
            return parsed && parsed.authenticated === true;
        } catch (error) {
            console.error('Could not read Upstar access state:', error);
            return false;
        }
    }

    function grantAccess() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({
            authenticated: true,
            username: TEST_USERNAME,
            grantedAt: Date.now()
        }));
    }

    function clearAccess() {
        localStorage.removeItem(STORAGE_KEY);
    }

    function getSafeRedirect(nextValue, fallback) {
        if (!nextValue) {
            return fallback;
        }

        try {
            const nextUrl = new URL(nextValue, window.location.origin);
            if (nextUrl.origin !== window.location.origin) {
                return fallback;
            }
            return nextUrl.pathname + nextUrl.search + nextUrl.hash;
        } catch (error) {
            console.warn('Ignoring invalid next redirect:', error);
            return fallback;
        }
    }

    function getLoginUrl() {
        const loginPath = CONFIG.loginPath || 'index.html';
        const loginUrl = new URL(loginPath, window.location.href);
        loginUrl.searchParams.set('next', window.location.pathname + window.location.search + window.location.hash);
        return loginUrl.toString();
    }

    function addLogoutButton() {
        if (document.querySelector('[data-upstar-logout]')) {
            return;
        }

        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = 'Log out';
        button.setAttribute('data-upstar-logout', 'true');
        button.style.cssText = [
            'position:fixed',
            'top:16px',
            'right:16px',
            'z-index:10050',
            'padding:10px 14px',
            'border:none',
            'border-radius:999px',
            'background:#1d4ed8',
            'color:#ffffff',
            'font:600 14px/1.2 system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif',
            'box-shadow:0 10px 25px rgba(29,78,216,0.28)',
            'cursor:pointer'
        ].join(';');
        button.addEventListener('click', function() {
            clearAccess();
            window.location.href = CONFIG.loginPath || 'index.html';
        });
        document.body.appendChild(button);
    }

    if (CONFIG.mode === 'protect') {
        if (!hasAccess()) {
            window.location.replace(getLoginUrl());
            return;
        }

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', addLogoutButton);
        } else {
            addLogoutButton();
        }
        return;
    }

    if (CONFIG.mode !== 'login') {
        return;
    }

    document.addEventListener('DOMContentLoaded', function() {
        const params = new URLSearchParams(window.location.search);
        const fallback = CONFIG.successPath || 'app.html';
        const nextTarget = getSafeRedirect(params.get('next'), fallback);

        if (hasAccess()) {
            window.location.replace(nextTarget);
            return;
        }

        const form = document.getElementById('upstar-login-form');
        const usernameInput = document.getElementById('upstar-username');
        const passwordInput = document.getElementById('upstar-password');
        const errorBox = document.getElementById('upstar-login-error');

        if (!form || !usernameInput || !passwordInput || !errorBox) {
            return;
        }

        form.addEventListener('submit', function(event) {
            event.preventDefault();
            errorBox.hidden = true;

            const username = usernameInput.value.trim();
            const password = passwordInput.value;

            if (username === TEST_USERNAME && password === TEST_PASSWORD) {
                grantAccess();
                window.location.href = nextTarget;
                return;
            }

            errorBox.hidden = false;
            passwordInput.value = '';
            passwordInput.focus();
        });
    });
})();

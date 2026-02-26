// ── YCCE-AI Auth Logic ────────────────────────────────────
(function () {
    'use strict';

    // --- Check if already logged in ---
    async function checkSession() {
        const { data: { session } } = await _sb.auth.getSession();
        if (session) {
            window.location.href = 'chat.html';
        }
    }
    checkSession();

    // --- DOM Elements ---
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const msgBox = document.getElementById('auth-message');

    // --- Tab Switching ---
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;

            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            if (tab === 'login') {
                loginForm.classList.remove('hidden');
                signupForm.classList.add('hidden');
            } else {
                loginForm.classList.add('hidden');
                signupForm.classList.remove('hidden');
            }

            hideMessage();
        });
    });

    // --- Show/Hide Messages ---
    function showMessage(text, type = 'error') {
        msgBox.textContent = text;
        msgBox.className = `auth-message ${type}`;
        msgBox.classList.remove('hidden');
    }

    function hideMessage() {
        msgBox.classList.add('hidden');
    }

    function setLoading(form, loading) {
        const btn = form.querySelector('.btn-primary');
        const span = btn.querySelector('span');
        const loader = btn.querySelector('.btn-loader');
        if (loading) {
            span.classList.add('hidden');
            loader.classList.remove('hidden');
            btn.disabled = true;
        } else {
            span.classList.remove('hidden');
            loader.classList.add('hidden');
            btn.disabled = false;
        }
    }

    // --- Login ---
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideMessage();

        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;

        if (!email || !password) {
            showMessage('Please fill in all fields.');
            return;
        }

        setLoading(loginForm, true);

        const { data, error } = await _sb.auth.signInWithPassword({
            email,
            password,
        });

        setLoading(loginForm, false);

        if (error) {
            showMessage(error.message);
        } else {
            window.location.href = 'chat.html';
        }
    });

    // --- Signup ---
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideMessage();

        const email = document.getElementById('signup-email').value.trim();
        const password = document.getElementById('signup-password').value;
        const confirm = document.getElementById('signup-confirm').value;

        if (!email || !password || !confirm) {
            showMessage('Please fill in all fields.');
            return;
        }

        if (password !== confirm) {
            showMessage('Passwords do not match.');
            return;
        }

        if (password.length < 6) {
            showMessage('Password must be at least 6 characters.');
            return;
        }

        setLoading(signupForm, true);

        const { data, error } = await _sb.auth.signUp({
            email,
            password,
        });

        setLoading(signupForm, false);

        if (error) {
            showMessage(error.message);
        } else if (data.user && !data.session) {
            showMessage('Account created! Check your email to verify, then log in.', 'success');
        } else {
            window.location.href = 'chat.html';
        }
    });
})();

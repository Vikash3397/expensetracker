# Spec: Login and Logout

## Overview

Implement session-based authentication so registered users can sign in with email and password and sign out when done. The login page template already exists; this step adds POST handling, password verification against stored hashes, Flask session management, and a working `/logout` route that replaces the Step 3 placeholder. Successful login establishes a server-side session keyed by `user_id` so later steps (profile, expenses) can identify the current user.

## Depends on

- **Step 01 — Database setup:** `users` table, `get_db()`, `init_db()`, and `seed_db()` with demo user `demo@spendly.com` / `demo123`.
- **Step 02 — Registration:** `get_user_by_email`, `create_user`, and hashed passwords via Werkzeug on the register flow.

## Routes

- `GET /login` — show the sign-in form; if already logged in, redirect to landing — **public**
- `POST /login` — validate credentials, set session, redirect on success or re-render with errors — **public**
- `GET /logout` — clear session and redirect to landing — **public** (safe to call when not logged in)

## Database changes

No database changes. Reuse `get_user_by_email(email)` from Step 2. Optionally add `get_user_by_id(user_id)` in `database/db.py` if needed for session validation or navbar display — no schema migration.

## Templates

- **Create:** none
- **Modify:** `templates/login.html`
  - Form `action` via `{{ url_for('login') }}` (no hardcoded `/login`)
  - On validation error, repopulate the email field from submitted values
  - Keep existing `{% if error %}` block for server-side messages
- **Modify:** `templates/base.html`
  - Navbar reflects auth state: when logged out, show “Sign in” and “Get started”; when logged in, show the user’s name (or email) and a “Log out” link to `url_for('logout')`
  - Use `session` (or a context variable injected from `app.py`) consistently — prefer a small pattern that later steps can reuse

## Files to change

- `app.py` — set `app.secret_key`; implement `GET`/`POST` on `/login`; replace `/logout` placeholder with session clear and redirect; optional `before_request` or helper to load current user for templates
- `database/db.py` — add `get_user_by_id(user_id)` only if required for login/session checks
- `templates/login.html` — `url_for` action and email field preservation
- `templates/base.html` — conditional navbar for logged-in vs logged-out users

## Files to create

None.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords verified with `check_password_hash` from Werkzeug against `password_hash` in the database — never compare plain text
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Set `app.secret_key` (e.g. from environment variable `SECRET_KEY` with a dev-only fallback documented in code) before using sessions or flashes
- Store minimal session data: at least `user_id`; optionally `name` for navbar display without an extra query on every request
- Normalise email to lowercase on POST before lookup (match registration behaviour)
- On invalid credentials, show a single generic error (e.g. “Invalid email or password”) — do not reveal whether the email exists
- On successful login, `redirect(url_for('landing'))` (profile dashboard is Step 4)
- On successful logout, `session.clear()` then redirect to landing
- Use `url_for` for all redirects and form actions — no hardcoded paths
- Do **not** implement profile, expense routes, or `@login_required` decorators beyond what login/logout need; leave `/profile` and expense placeholders unchanged
- Do not change register behaviour except shared helpers if extracted
- Minimal diff — no unrelated refactors

## Definition of done

- [ ] `GET /login` renders the sign-in page with unchanged layout
- [ ] Valid POST with `demo@spendly.com` / `demo123` sets a session and redirects to the landing page
- [ ] Navbar shows logged-in state (user name or email) and a working “Log out” link after login
- [ ] `GET /logout` clears the session and redirects to landing; navbar returns to logged-out links
- [ ] POST with wrong password or unknown email re-renders login with an error and preserved email
- [ ] Logged-in user visiting `GET /login` is redirected away (e.g. to landing)
- [ ] Login form posts to `url_for('login')`, not a hardcoded path
- [ ] `/logout` no longer returns placeholder stub text
- [ ] App starts with `python app.py` on port 5001 without errors
- [ ] Placeholder routes `/profile` and `/expenses/...` remain stubs

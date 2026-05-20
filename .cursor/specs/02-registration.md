# Spec: Registration

## Overview

Wire up user registration so new visitors can create a Spendly account. The register page and form already exist as static templates; this step adds server-side validation, password hashing, and persistence to the `users` table from Step 1. Successful sign-up redirects to the login page (session-based login remains Step 3).

## Depends on

- **Step 01 — Database setup:** `users` table, `get_db()`, `init_db()`, and `seed_db()` in `database/db.py` must be working.

## Routes

- `GET /register` — show the registration form — **public**
- `POST /register` — validate input, create user, redirect on success or re-render with errors — **public**

## Database changes

No database changes. The `users` table already has `name`, `email`, `password_hash`, and `created_at` with a unique constraint on `email`.

Add helper functions in `database/db.py` only (no schema migration):

- `get_user_by_email(email)` — return user row or `None`
- `create_user(name, email, password_hash)` — insert one user; let SQLite raise on duplicate email if not checked earlier

## Templates

- **Create:** none
- **Modify:** `templates/register.html`
  - Set form `action` to `{{ url_for('register') }}` (no hardcoded `/register`)
  - On validation error, repopulate `name` and `email` fields from submitted values
  - Keep existing `{% if error %}` block for server-side messages

## Files to change

- `app.py` — accept `GET` and `POST` on `/register`; validate; call DB helpers; redirect to login on success
- `database/db.py` — add `get_user_by_email` and `create_user`
- `templates/register.html` — `url_for` action and field value preservation

## Files to create

None.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (`generate_password_hash`) before insert; never store plain text
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `url_for` for redirects and form actions — no hardcoded paths
- Server-side validation only (do not rely on HTML5 alone): name non-empty, valid email format, password minimum 8 characters
- Normalise email to lowercase before lookup and insert
- On duplicate email, show a clear error (e.g. “An account with this email already exists”) — do not expose whether the email exists in other ways
- Do **not** implement login POST, Flask sessions, or auto-login in this step
- On success, redirect to `url_for('login')` with an optional flash message (set `app.secret_key` for flashes if used)
- Do not modify placeholder routes (`/logout`, `/profile`, `/expenses/...`)
- Minimal diff — no unrelated refactors

## Definition of done

- [ ] `GET /register` renders the registration page unchanged in layout
- [ ] Valid POST (new unique email, password ≥ 8 chars) inserts a user with a hashed password in `expense_tracker.db`
- [ ] After successful registration, browser is redirected to the login page
- [ ] POST with missing/invalid fields re-renders the form with an `error` message and preserved name/email
- [ ] POST with an email already in the database (e.g. `demo@spendly.com`) shows a duplicate-email error without creating a row
- [ ] Form posts to `url_for('register')`, not a hardcoded path
- [ ] App starts with `python app.py` on port 5001 without errors
- [ ] No changes to login/logout behaviour beyond the post-registration redirect target

# Spec: Profile

## Overview

Replace the `/profile` placeholder with a logged-in account page where users can view their details, update their name and email, and change their password. This step introduces route protection (`login_required`) so only authenticated users can access the profile, and reuses the session from Step 3 (`user_id`) to load and update the correct row in `users`. Expense routes remain stubs until later steps.

## Depends on

- **Step 01 — Database setup:** `users` table and `get_db()`.
- **Step 02 — Registration:** `create_user`, `get_user_by_email`, password hashing patterns.
- **Step 03 — Login and logout:** Flask sessions with `user_id` and `user_name`; working `/login` and `/logout`.

## Routes

- `GET /profile` — show account details and edit forms — **logged-in** (redirect to login if no session)
- `POST /profile` — update name and email — **logged-in**
- `POST /profile/password` — change password (current + new) — **logged-in**

## Database changes

No database changes. The `users` table already has `name`, `email`, `password_hash`, and `created_at`.

Add helper functions in `database/db.py` only (no schema migration):

- `get_user_by_id(user_id)` — return user row or `None`
- `update_user(user_id, name, email)` — update name and email for one user
- `update_user_password(user_id, password_hash)` — update `password_hash` for one user

## Templates

- **Create:** `templates/profile.html`
  - Extends `base.html`; app-page layout per `.cursor/skills/frontend-design/SKILL.md` (page header + card)
  - Display read-only **Member since** from `created_at` (formatted for display)
  - Form 1: update **name** and **email** — `POST` to `url_for('profile')`
  - Form 2: change password — **current password**, **new password**, **confirm new password** — `POST` to `url_for('profile_password')` (or equivalent view name)
  - Server-side `{% if error %}` / `{% if success %}` (or separate error keys per form) for validation messages
  - Repopulate fields from submitted values on error
- **Modify:** `templates/base.html`
  - When logged in, make the user name (or “Profile”) a link to `url_for('profile')`

## Files to change

- `app.py` — `login_required` helper; replace `/profile` stub; add `POST /profile` and `POST /profile/password`; load user from session; validation and redirects
- `database/db.py` — `get_user_by_id`, `update_user`, `update_user_password`
- `templates/base.html` — profile link in navbar for logged-in users
- `static/css/style.css` — append app-page / profile section styles (use design tokens; follow frontend-design skill)

## Files to create

- `templates/profile.html`

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with Werkzeug (`generate_password_hash`); verify current password with `check_password_hash` before updating
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Implement a small `login_required` decorator (or equivalent) on profile routes; unauthenticated requests redirect to `url_for('login')`
- Load the current user with `get_user_by_id(session['user_id'])`; if missing (stale session), `session.clear()` and redirect to login
- **Update profile:** name non-empty; valid email format; normalise email to lowercase; if email changed, ensure it is not taken by another user (`get_user_by_email` excluding self)
- On successful name/email update, refresh `session['user_name']` if name changed
- **Change password:** require current password; new password minimum 8 characters; new and confirm must match; generic error if current password is wrong
- Use `url_for` for all form actions and redirects — no hardcoded paths
- Do **not** implement expense routes, expense list UI, or global `before_request` auth on every route — protect `/profile` routes only
- Do not change login redirect target (stay on landing after login unless product decision is documented in plan)
- Follow `.cursor/skills/frontend-design/SKILL.md` for profile page layout
- Minimal diff — no unrelated refactors

## Definition of done

- [ ] Unauthenticated `GET /profile` redirects to the login page
- [ ] Logged-in `GET /profile` shows name, email, and member-since date for the session user
- [ ] Valid `POST /profile` updates name and/or email in the database and shows success; navbar name updates if name changed
- [ ] `POST /profile` with an email already used by another account shows an error without updating
- [ ] Valid `POST /profile/password` with correct current password updates the hash; user can sign in with the new password
- [ ] Wrong current password on password change shows an error; password in DB unchanged
- [ ] Navbar links to profile when logged in (e.g. user name → profile)
- [ ] `/profile` no longer returns placeholder stub text
- [ ] Forms use `url_for`, not hardcoded paths
- [ ] App starts with `python app.py` on port 5001 without errors
- [ ] `/expenses/...` placeholder routes remain stubs

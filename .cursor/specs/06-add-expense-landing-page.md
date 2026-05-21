# Spec: Add Expense on Landing Page

## Overview

Let logged-in users **record a new expense directly on the landing dashboard** (`GET /`) without visiting a separate page. The dashboard already shows spending totals, category breakdown, date filtering, and an expense table; this step adds an **“Add expense”** form on that same view and persists rows to the `expenses` table for the session user. It delivers the “log expenses instantly” promise from the marketing copy and unblocks real user data on the dashboard. The standalone `/expenses/add` route stays a stub until a later step.

## Depends on

- **Step 01 — Database setup:** `expenses` table, `get_db()`, `init_db()`, `seed_db()`.
- **Step 02 — Registration:** user accounts.
- **Step 03 — Login and logout:** Flask session with `user_id`.
- **Step 04 — Profile:** `login_required` pattern, `_get_current_user()`, session handling.
- **Step 05 — Date filter (landing dashboard):** logged-in `GET /` with optional `from` / `to` query params, `_load_user_spending()`, and expense query helpers with optional date bounds.

## Routes

- `GET /` — unchanged behaviour: public marketing page when logged out; logged-in dashboard with spending summary and date filter — **public** (dashboard section requires session)
- `POST /` — accept and validate a new expense for the logged-in user; on success redirect to `GET /` (preserve active `from` / `to` query params when present); on validation error re-render the dashboard with errors and repopulated fields — **logged-in** (redirect to login if no session)

No other new routes. `/expenses/add`, `/expenses/<id>/edit`, and `/expenses/<id>/delete` remain stubs.

## Database changes

No schema changes. Add one helper in `database/db.py`:

- `create_expense(user_id, amount, category, date, description=None)` — `INSERT` into `expenses` with parameterised values; return the new row `id` (or `lastrowid`)

## Templates

- **Create:** none
- **Modify:** `templates/landing.html` (logged-in branch only)
  - Add an **“Add expense”** `data-card` above or beside the filter/summary area (clear visual hierarchy; follow `.cursor/skills/frontend-design/SKILL.md`)
  - Form: `method="POST"` `action="{{ url_for('landing') }}"`
  - Fields: **amount** (`type="number"`, `step="0.01"`, `min="0.01"`), **category** (`<select>` with fixed options), **date** (`type="date"`), **description** (`type="text"`, optional)
  - When a date filter is active, include hidden inputs `from` and `to` so a successful POST redirect can restore the same filter
  - Show `expense_error` in `auth-error` styling; repopulate submitted values on error
  - Optional short success hint (`expense_success`) after redirect (query param or flash — prefer a simple `?added=1` query flag cleared on next navigation if flash is not used elsewhere)

## Files to change

- `app.py` — extend `landing()` to handle `POST`: validate input, call `create_expense`, redirect or re-render with spending data and filter state; protect POST with the same session rules as the logged-in dashboard
- `database/db.py` — `create_expense`
- `templates/landing.html` — add-expense form in logged-in dashboard
- `static/css/style.css` — append styles for the add-expense form layout (grid or stacked `form-group`s inside `data-card`); use design tokens only

## Files to create

None.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (unchanged this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- **Categories:** allow only a fixed list matching seed data: `Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other` — validate server-side; reject unknown values
- **Amount:** required; must parse to a positive number (`> 0`); reject empty, zero, negative, and non-numeric input with a clear `expense_error`
- **Date:** required; validate as `YYYY-MM-DD` (`datetime.strptime`); store as `TEXT` in that format
- **Description:** optional; strip whitespace; empty string stored as `NULL` or `''` consistently with existing rows
- **Auth:** unauthenticated `POST /` redirects to `url_for('login')`; use `session['user_id']` for `create_expense`
- On success: `redirect(url_for('landing', from=…, to=…))` when filter params were active; otherwise `redirect(url_for('landing'))`
- On error: re-run the same spending/filter loading as `GET` so totals and table stay in sync; pass `expense_error` and field repopulation values into the template
- Do **not** implement `/expenses/add` or edit/delete routes in this step
- Do **not** change profile routes or `templates/profile.html` unless required for a shared helper extraction in `app.py`
- Use `url_for` for form `action` and redirects — no hardcoded paths
- Reuse existing classes: `data-card`, `form-group`, `form-input`, `btn-primary`, `auth-error`
- Follow `.cursor/skills/frontend-design/SKILL.md` for form and dashboard layout
- Minimal diff — no unrelated refactors

## Definition of done

- [ ] Logged-in `GET /` shows an add-expense form on the dashboard with amount, category, date, and description fields
- [ ] Valid `POST /` inserts one row into `expenses` for the session user and redirects to the dashboard; the new expense appears in the table and updates total and category breakdown
- [ ] `POST /` with missing or invalid amount, category, or date shows `expense_error` and repopulates the form without losing the current date filter
- [ ] `POST /` with an invalid category value is rejected server-side
- [ ] Unauthenticated `POST /` redirects to login
- [ ] Active `from` / `to` filters on the dashboard are preserved after a successful add (same filtered view)
- [ ] Logged-out `GET /` marketing page is unchanged (no add-expense form)
- [ ] `/expenses/add` still returns the Step 7 stub text; edit and delete routes remain stubs
- [ ] All SQL uses bound parameters
- [ ] App starts with `python app.py` on port 5001 without errors

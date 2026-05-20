# Spec: Date Filter For Profile Page

## Overview

Extend the logged-in profile page with a **spending summary** section so users can review their expenses in context while managing their account. A **date-range filter** (optional `from` and `to` query parameters on `GET /profile`) narrows totals, category breakdown, and the expense table to expenses whose `date` falls within the range. This step delivers the “filter by time period” capability advertised on the landing page, without changing the landing dashboard or expense CRUD stubs.

## Depends on

- **Step 01 — Database setup:** `expenses` table, `get_db()`, seed data.
- **Step 02 — Registration:** user accounts.
- **Step 03 — Login and logout:** session with `user_id`.
- **Step 04 — Profile:** working `/profile`, `login_required`, account update forms, and existing expense query helpers (`get_expenses_for_user`, `get_expense_total_for_user`, `get_category_totals_for_user`) used on the landing dashboard.

## Routes

- `GET /profile` — existing profile page; **extend** to accept optional query params `from` and `to` (ISO dates `YYYY-MM-DD`) to filter the spending section — **logged-in**
- `POST /profile` — unchanged (account details) — **logged-in**
- `POST /profile/password` — unchanged — **logged-in**

No new routes.

## Database changes

No database changes. Extend query helpers in `database/db.py` to accept optional `from_date` and `to_date` (both `None` = no date filter):

- `get_expenses_for_user(user_id, from_date=None, to_date=None)`
- `get_expense_total_for_user(user_id, from_date=None, to_date=None)`
- `get_category_totals_for_user(user_id, from_date=None, to_date=None)`

Filter with parameterised SQL on `expenses.date` (stored as `TEXT` in `YYYY-MM-DD` form). When both bounds are provided, use `date >= ? AND date <= ?`. When only one bound is provided, apply that single bound. Order and columns for the list query stay the same as today.

## Templates

- **Create:** none
- **Modify:** `templates/profile.html`
  - Add a **“Your spending”** section below the account/password cards (or in a clear third block within `page-body`)
  - **Filter form:** `method="GET"` `action="{{ url_for('profile') }}"` — fields `from` and `to` as `type="date"` inputs; submit button to apply filter; link or button to **Clear filter** (`url_for('profile')` with no query params)
  - Optional preset links (same GET pattern): e.g. “All time”, “This month” — compute month bounds server-side and pass as query string
  - Show `filter_error` when dates are invalid or `from` > `to`
  - Reuse landing dashboard markup/classes where possible: `data-card`, `dashboard-total`, `mock-bars` / category rows, `expense-table`, `empty-state`, `inr` filter
  - Display active range in subtitle copy when filtered (e.g. “Showing 2026-05-01 to 2026-05-15”)
  - Preserve existing account and password forms unchanged

## Files to change

- `app.py` — on `GET /profile`, read and validate `from` / `to` from `request.args`; load filtered expenses, total, and category totals; build `category_bars` the same way as `landing()`; pass filter state and errors into `_render_profile`
- `database/db.py` — optional date-range parameters on the three expense query helpers
- `templates/profile.html` — spending section + date filter UI
- `static/css/style.css` — append styles for date-filter row (layout, inputs, clear link); use design tokens only

## Files to create

None.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- **Scope:** date filter and spending widgets on **profile only** — do not add filtering to `GET /` landing in this step
- Validate `from` and `to` as `YYYY-MM-DD` (regex or `datetime.strptime`); reject invalid dates with a user-visible `filter_error` and show unfiltered data (or empty filter fields) — do not crash
- If only one of `from` / `to` is supplied, filter with that bound only; if both supplied, require `from <= to`
- Default when no valid filter: show **all** expenses for the user (same as current landing behaviour)
- Use `url_for('profile', from=…, to=…)` for preset links — no hardcoded paths
- Keep `login_required` on profile routes; use `_get_current_user()` as today
- Account `POST` handlers must ignore date query params on redirect/re-render (no need to preserve filter on POST unless re-displaying GET section — after POST success, returning profile without query params is acceptable)
- Reuse `_format_inr` and category bar width logic from `landing()` — extract a small shared helper in `app.py` if it avoids duplication, but avoid unrelated refactors
- Follow `.cursor/skills/frontend-design/SKILL.md` for app-page layout and form patterns
- Do **not** implement expense add/edit/delete routes or change placeholder expense routes
- Minimal diff — no drive-by changes to `templates/landing.html` unless required for shared helper extraction

## Definition of done

- [ ] Logged-in `GET /profile` without query params shows all user expenses in the new spending section (total, categories if any, table)
- [ ] `GET /profile?from=2026-05-01&to=2026-05-10` shows only expenses with `date` in that inclusive range; total and category breakdown match the filtered set
- [ ] Invalid date strings or `from` after `to` show a clear `filter_error` and do not break the page; account forms still work
- [ ] “Clear filter” (or equivalent) returns the full unfiltered spending view
- [ ] Date inputs repopulate with the submitted `from` / `to` values after apply
- [ ] `POST /profile` and `POST /profile/password` still update account details and password as in Step 04
- [ ] Unauthenticated access to `/profile` still redirects to login
- [ ] Landing dashboard (`GET /`) behaviour is unchanged (no date filter there yet)
- [ ] All SQL uses bound parameters; no string-concatenated user input in queries
- [ ] App starts with `python app.py` on port 5001 without errors
- [ ] `/expenses/...` placeholder routes remain stubs

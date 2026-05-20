---
description: General project standards for the Spendly expense tracker (Flask, templates, static assets, SQLite)
alwaysApply: true
---

# Spendly — General Project Rules

## 1. Overview of the project

**Spendly** is a personal expense tracker for logging spending, viewing patterns, and managing finances. It is built as a **step-by-step learning project**: some routes and `database/db.py` are stubs until later steps.

| Aspect | Detail |
|--------|--------|
| Stack | **Flask 3.x**, **Jinja2**, **SQLite**, vanilla **HTML/CSS/JS** |
| Run | `python app.py` on **port 5001** (`debug=True`) |
| Locale | Indian rupees (**₹**) in copy and amounts |
| Brand | Spendly — DM Sans (body), DM Serif Display (headings), green accent palette |

**Implemented today:** landing, register, and login pages (templates + styles). **Planned in later steps:** auth (logout), profile, expense CRUD, full database layer in `database/db.py`.

Reference canonical UI patterns in `@templates/base.html`, `@templates/landing.html`, and `@static/css/style.css` before adding new pages.

---

## 2. Architecture layout (high level)

```
Browser
   │
   ▼
app.py                    ← Flask app, @app.route handlers, render_template / redirects
   │
   ├── templates/        ← Jinja2; every page extends base.html
   │     base.html       ← navbar, main, footer, static asset links
   │     landing.html, login.html, register.html, …
   │
   ├── static/
   │     css/style.css   ← design tokens (:root), global layout & components
   │     js/main.js      ← client-side behavior
   │
   └── database/
         db.py           ← SQLite: get_db(), init_db(), seed_db() (Step 1+)
         expense_tracker.db   ← runtime DB file (gitignored)
```

| Path | Responsibility |
|------|----------------|
| `app.py` | Route registration; thin handlers that render templates or redirect |
| `database/db.py` | Connection factory, schema (`CREATE TABLE IF NOT EXISTS`), dev seed data |
| `templates/` | Server-rendered HTML; blocks: `title`, `content`, optional `head` / `scripts` |
| `static/css/style.css` | Single stylesheet; CSS variables and sectioned rules |
| `static/js/main.js` | Shared client scripts |
| `requirements.txt` | `flask`, `werkzeug`, `pytest`, `pytest-flask` |

**Request flow:** HTTP → Flask route → (optional DB via `get_db()`) → Jinja2 template → HTML + static assets.

**Route groups in `app.py`:** live routes (`/`, `/register`, `/login`) and **placeholder** routes (`/logout`, `/profile`, `/expenses/...`) that return stub text until the matching step — implement placeholders only when the task requires it.

---

## 3. Code style to follow

### Python & Flask

- Register routes in `app.py` with `@app.route(...)`; return `render_template("….html")` or redirects.
- Use **`url_for('view_function_name')`** in templates and Python — never hardcode paths like `/login`.
- Group routes with the same `# ------------------------------------------------------------------ #` comment blocks as in `app.py`.
- Match existing naming: view functions named after the page (`landing`, `register`, `login`).

### Templates (Jinja2)

- Every page **`{% extends "base.html" %}`** and fills `{% block title %}`, `{% block content %}`, and optionally `{% block head %}` / `{% block scripts %}`.
- Reuse existing classes (`btn-primary`, `btn-ghost`, `auth-card`, `hero`, etc.) — do not invent parallel button/card systems.
- Use semantic HTML: `nav`, `main`, `footer`, `section`, `form`, `label`.
- Extend existing markup (navbar, footer) rather than removing or refactoring working layout unless asked.

### CSS & UI

- Use **CSS variables** from `:root` in `style.css` (`--ink`, `--paper`, `--accent`, `--font-body`, etc.) — no one-off hex when a token exists.
- Add styles in **dedicated sections** with `/* ---- */` headers; **append** selectors instead of rewriting existing rules.
- Preserve **responsive** behavior; follow existing `@media` breakpoints.
- Keep layout cohesive: centered max-width content, sticky navbar, dark footer on `--ink`.

### Database

- Logic in `database/db.py`: `get_db()` with `row_factory` and **foreign keys enabled**; `init_db()` with `CREATE TABLE IF NOT EXISTS`; `seed_db()` for dev sample data.
- Use **parameterized SQL** only — no string-concatenated queries.

### Changes & quality

- **Minimal, task-focused diffs** — no drive-by refactors, unrelated files, or new markdown unless requested.
- Read surrounding code first; match naming, structure, and comment style.
- Use **pytest** / **pytest-flask** when tests are in scope; run tests or start the app after substantive changes.

---

## 4. Critical rules (do / avoid)

### Do

- Validate and sanitize user input **server-side** when forms and auth are implemented.
- Hash passwords (e.g. Werkzeug) and use **Flask sessions** for auth — never store plain-text passwords.
- Keep secrets and runtime data out of git: `.env`, credentials, `expense_tracker.db` (see `.gitignore`).
- Commit or push **only when the user explicitly asks**; never change git config on the user’s behalf.
- Implement placeholder routes **only** when the current task requires that step.

### Avoid

- Hardcoded URL paths in templates or redirects (use `url_for`).
- SQL built from string concatenation with user input.
- Committing `.env`, credentials, or the SQLite database file.
- Large unrelated refactors, deleting working navbar/footer markup, or inventing duplicate CSS component classes.
- Introducing one-off colors when a design token already exists in `:root`.
- Implementing stub routes (logout, profile, expenses) ahead of the step that owns them.

### Security & forms (when implemented)

- Server-side validation on all POST handlers.
- Session-based auth with secure cookie settings appropriate to deployment.
- Parameterized queries for every DB read/write involving user data.

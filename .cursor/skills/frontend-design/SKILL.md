---
name: frontend-design
description: >-
  Designs and implements Spendly frontend pages (Jinja2 templates, style.css)
  following the project's visual system. Use when creating or updating HTML
  templates, CSS, landing/marketing sections, auth forms, dashboards, expense
  lists, profile UI, or when the user asks for page design, layout, or styling
  for this expense tracker.
---

# Spendly Frontend Design

Build pages that look like they shipped with Spendly — warm paper backgrounds, green accent, serif display headings, and existing component classes.

## Before you code

1. Read canonical references (do not guess styles):
   - `templates/base.html` — layout shell, navbar, footer, blocks
   - `templates/landing.html` — marketing hero, features, CTA
   - `templates/login.html` / `register.html` — auth pattern
   - `static/css/style.css` — tokens and components
2. Pick a **page archetype** (see [reference.md](reference.md)):
   - **Marketing** — hero + optional features/CTA
   - **Auth** — centered `auth-section` + `auth-card` form
   - **App** — page header + card/list/table inside `main-content`
3. Reuse existing classes first; add CSS only when no class fits.

## Non-negotiables

| Rule | Detail |
|------|--------|
| Extend base | Every page `{% extends "base.html" %}` with `title` + `content` blocks |
| URLs | `url_for('view_name')` only — never hardcode `/login` etc. |
| Tokens | Colors, fonts, radii from `:root` in `style.css` — no one-off hex |
| Currency | Indian rupees: `₹12,450` in copy and amounts |
| Brand | **Spendly**, ◈ icon, tagline tone: clear, calm, personal finance |
| Scope | Append CSS in new `/* ---- */` sections; do not rewrite working rules |
| Navbar/footer | Do not remove or restyle global chrome unless explicitly asked |

## Design tokens (quick reference)

| Token | Use |
|-------|-----|
| `--ink` / `--ink-muted` / `--ink-faint` | Text hierarchy |
| `--paper` / `--paper-warm` / `--paper-card` | Page bg, sections, cards |
| `--accent` / `--accent-light` | Primary brand, badges, links |
| `--accent-2` | Secondary highlight (footer icon, chart bars) |
| `--danger` / `--danger-light` | Errors (`auth-error`) |
| `--font-display` | Page titles (`hero-title`, `auth-title`, `cta-title`) |
| `--font-body` | Body, labels, buttons |
| `--max-width` | Content width (1200px) |
| `--auth-width` | Auth column (440px) |
| `--radius-sm` / `--md` / `--lg` | Buttons, cards, mock UI |

Fonts load in `base.html` (DM Sans + DM Serif Display). Do not add competing font stacks.

## Component catalog

Reuse these before inventing new ones:

| Class | Role |
|-------|------|
| `btn-primary` / `btn-ghost` | Primary and secondary actions (links or buttons) |
| `btn-submit` | Full-width form submit |
| `hero`, `hero-badge`, `hero-title`, `hero-subtitle`, `hero-actions` | Landing hero |
| `mock-card`, `mock-bar-*` | Decorative expense preview (landing only) |
| `features`, `feature-card`, `feature-icon` | Three-column feature grid |
| `cta-section`, `cta-title`, `cta-body` | Bottom signup CTA |
| `auth-section`, `auth-container`, `auth-header`, `auth-card` | Auth layout |
| `form-group`, `form-input`, `auth-error`, `auth-switch` | Forms |
| `nav-brand`, `nav-cta`, `footer` | Global chrome (in base) |

New app UI (expenses, profile): prefer **card-on-paper** — white `paper-card`, `1px solid var(--border)`, `border-radius: var(--radius-md)`, generous padding — matching `auth-card` and `feature-card`.

## Page-building workflow

Copy this checklist and track progress:

```
- [ ] Archetype chosen (marketing / auth / app)
- [ ] Template extends base.html; title block set
- [ ] Semantic HTML: section, h1, form, label[for]
- [ ] Existing component classes used
- [ ] New CSS appended in dedicated section (if needed)
- [ ] Responsive: checked @media 900px and 600px patterns
- [ ] Flask route uses render_template (if new page)
```

### Step 1 — Template skeleton

```jinja2
{% extends "base.html" %}

{% block title %}Page title — Spendly{% endblock %}

{% block content %}
<section class="…">
    …
</section>
{% endblock %}
```

Title pattern: `{Action or page} — Spendly` (e.g. `Sign in — Spendly`, `Your expenses — Spendly`).

### Step 2 — Structure by archetype

**Auth:** `auth-section` → `auth-container` → `auth-header` + `auth-card` (form inside) + `auth-switch` link. Mirror `login.html` / `register.html`.

**Marketing:** `hero` (optional `hero-visual` / `mock-card`), then `features`, then `cta-section`. Mirror `landing.html`.

**App:** Use a top **page header** (new or reuse display font):

- `h1` with `font-family: var(--font-display)` at ~1.75–2rem
- Muted subtitle with `--ink-muted`
- Primary action as `btn-primary` aligned right on desktop (flex header)

Content below: cards, tables, or empty states. Keep max-width `var(--max-width)` centered with horizontal padding `2rem` (match hero).

### Step 3 — Forms

- `method="POST"` + `action="{{ url_for('…') }}"`
- Each field: `form-group` → `label[for]` + `input.form-input` with matching `id`/`name`
- Preserve values on error: `value="{{ field or '' }}"`
- Server errors: single `auth-error` block above the form (works for any page)
- Submit: `button.btn-submit` (auth) or `btn-primary` (inline actions)

### Step 4 — CSS additions

When new layout is required:

1. Add a section header: `/* ------------------------------------------------------------------ */` + `/* Page name */`
2. Use only `var(--…)` tokens
3. Add responsive rules in the existing `@media (max-width: 900px)` / `600px` blocks **or** extend them consistently
4. Prefer grid/flex patterns already used (hero 2-col, features 3-col, auth centered flex)

### Step 5 — Empty and error states

- **Empty:** Short display heading + muted body + one `btn-primary` CTA
- **Errors:** `auth-error` styling (or same classes) — never raw red inline styles
- **Success flash:** Reuse `auth-error` pattern with `--accent-light` background and `--accent` text if flash UI is added later

## Typography and voice

- **Headlines:** DM Serif Display; use `<em>` inside `hero-title` for accent emphasis (green italic)
- **Body:** 0.9–1.05rem, `--ink-muted` for secondary copy
- **Labels:** 0.85rem, `--ink-soft`, font-weight 500
- **Tone:** Direct, friendly, India-aware (rupees, sensible examples like `nitish@example.com`)

## Accessibility and quality

- One `h1` per page; logical heading order
- Associate every input with a `label`
- Sufficient contrast: text on `--paper-card` uses `--ink` / `--ink-muted`
- Touch targets: buttons ≥ ~44px height (existing padding meets this)
- After changes: run `python app.py`, open page at port **5001**, resize to mobile width

## What not to do

- No Tailwind, Bootstrap, or second CSS framework
- No duplicate button systems (`button-primary`, `card-form`, etc.)
- No inline `style=""` except mock bar widths on landing (`mock-bar`)
- No new global navbar/footer markup in child templates
- No implementing stub routes unless the task includes backend work

## Additional resources

- Full archetype HTML snippets and app-page CSS starters: [reference.md](reference.md)
- Project-wide rules: `.cursor/rules/general.md`

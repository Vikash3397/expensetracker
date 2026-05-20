# Spendly Frontend — Reference Templates

Copy and adapt these snippets. Replace placeholders in `ALL_CAPS`.

---

## Auth page (full content block)

```jinja2
<section class="auth-section">
    <div class="auth-container">

        <div class="auth-header">
            <h1 class="auth-title">PAGE_HEADING</h1>
            <p class="auth-subtitle">PAGE_SUBTITLE</p>
        </div>

        <div class="auth-card">
            {% if error %}
            <div class="auth-error">{{ error }}</div>
            {% endif %}

            <form method="POST" action="{{ url_for('ROUTE_VIEW') }}">
                <div class="form-group">
                    <label for="FIELD_ID">Label</label>
                    <input type="text" id="FIELD_ID" name="FIELD_NAME"
                           class="form-input" placeholder="Example"
                           value="{{ field_name or '' }}" required>
                </div>
                <button type="submit" class="btn-submit">BUTTON_LABEL</button>
            </form>
        </div>

        <p class="auth-switch">
            SWITCH_COPY
            <a href="{{ url_for('OTHER_VIEW') }}">Link text</a>
        </p>

    </div>
</section>
```

---

## Marketing — feature card row

```jinja2
<section class="features">
    <div class="features-inner">
        <div class="feature-card">
            <div class="feature-icon">₹</div>
            <h3 class="feature-title">TITLE</h3>
            <p class="feature-body">DESCRIPTION</p>
        </div>
    </div>
</section>
```

---

## App page — header + card list

```jinja2
{% extends "base.html" %}

{% block title %}Your expenses — Spendly{% endblock %}

{% block content %}

<section class="page-header-section">
    <div class="page-header-inner">
        <div class="page-header-text">
            <h1 class="page-title">Your expenses</h1>
            <p class="page-subtitle">Track and review your spending</p>
        </div>
        <a href="{{ url_for('add_expense') }}" class="btn-primary">Add expense</a>
    </div>
</section>

<section class="page-body">
    <div class="page-body-inner">
        {% if expenses %}
        <div class="data-card">
            <!-- table or list -->
        </div>
        {% else %}
        <div class="empty-state">
            <h2 class="empty-title">No expenses yet</h2>
            <p class="empty-body">Log your first expense to see it here.</p>
            <a href="{{ url_for('add_expense') }}" class="btn-primary">Add expense</a>
        </div>
        {% endif %}
    </div>
</section>

{% endblock %}
```

---

## App page — CSS starter (append to style.css)

```css
/* ------------------------------------------------------------------ */
/* App pages — shared                                                */
/* ------------------------------------------------------------------ */

.page-header-section {
    padding: 3rem 2rem 1.5rem;
    border-bottom: 1px solid var(--border);
}

.page-header-inner {
    max-width: var(--max-width);
    margin: 0 auto;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 1.5rem;
    flex-wrap: wrap;
}

.page-title {
    font-family: var(--font-display);
    font-size: clamp(1.75rem, 3vw, 2.25rem);
    color: var(--ink);
    margin-bottom: 0.35rem;
}

.page-subtitle {
    font-size: 0.95rem;
    color: var(--ink-muted);
}

.page-body {
    padding: 2rem;
}

.page-body-inner {
    max-width: var(--max-width);
    margin: 0 auto;
}

.data-card {
    background: var(--paper-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.5rem 2rem;
}

.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    background: var(--paper-card);
    border: 1px dashed var(--border);
    border-radius: var(--radius-md);
}

.empty-title {
    font-family: var(--font-display);
    font-size: 1.35rem;
    margin-bottom: 0.5rem;
}

.empty-body {
    font-size: 0.9rem;
    color: var(--ink-muted);
    margin-bottom: 1.5rem;
}

@media (max-width: 600px) {
    .page-header-inner {
        flex-direction: column;
        align-items: stretch;
    }

    .page-header-inner .btn-primary {
        text-align: center;
    }
}
```

---

## Expense amounts

- Prefix with `₹`; use grouping: `₹12,450`
- Large totals: `font-family: var(--font-display)` (see `.mock-total`)

---

## Navbar session states (in base.html)

| State | Nav shows |
|-------|-----------|
| Guest | Sign in + Get started (`nav-cta`) |
| Logged in | User name + Log out |

Do not duplicate navbar in child templates.

---

## Jinja blocks

| Block | Use |
|-------|-----|
| `{% block head %}` | Page-specific `<link>` or `<meta>` |
| `{% block scripts %}` | Page JS after `main.js` |

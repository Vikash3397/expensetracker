import calendar
import math
import os
from datetime import datetime
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import (
    create_expense,
    create_user,
    get_category_totals_for_user,
    get_expense_total_for_user,
    get_expenses_for_user,
    get_user_by_email,
    get_user_by_id,
    init_db,
    seed_db,
    update_user,
    update_user_password,
)

app = Flask(__name__)
# Set SECRET_KEY in the environment for production deployments.
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

with app.app_context():
    init_db()
    seed_db()

ALLOWED_CATEGORIES = (
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
)

MAX_EXPENSE_DESCRIPTION_LENGTH = 500


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def _get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = get_user_by_id(user_id)
    if user is None:
        session.clear()
    return user


def _is_valid_email(email):
    if "@" not in email:
        return False
    domain = email.split("@", 1)[1]
    return "." in domain


def _format_member_since(created_at):
    if not created_at:
        return ""
    return created_at[:10]


def _format_inr(amount):
    if amount == int(amount):
        return f"₹{int(amount):,}"
    return f"₹{amount:,.2f}"


app.jinja_env.filters["inr"] = _format_inr


def _parse_date_arg(value):
    if not value or not value.strip():
        return None, None
    try:
        datetime.strptime(value.strip(), "%Y-%m-%d")
        return value.strip(), None
    except ValueError:
        return None, "Please use dates in YYYY-MM-DD format."


def _resolve_date_filter_values(raw_from, raw_to):
    if not raw_from and not raw_to:
        return None, None, None, None, None

    filter_error = None
    from_date = None
    to_date = None

    if raw_from:
        from_date, err = _parse_date_arg(raw_from)
        if err:
            filter_error = err
    if raw_to and not filter_error:
        to_date, err = _parse_date_arg(raw_to)
        if err:
            filter_error = err

    if not filter_error and from_date and to_date and from_date > to_date:
        filter_error = "Start date must be on or before end date."

    if filter_error:
        return None, None, raw_from, raw_to, filter_error

    return from_date, to_date, raw_from or None, raw_to or None, None


def _build_filter_label(from_date, to_date):
    if from_date and to_date:
        return f"Showing {from_date} to {to_date}"
    if from_date:
        return f"Showing from {from_date}"
    if to_date:
        return f"Showing through {to_date}"
    return None


def _month_preset_bounds():
    now = datetime.now()
    last_day = calendar.monthrange(now.year, now.month)[1]
    return {
        "from": now.replace(day=1).strftime("%Y-%m-%d"),
        "to": now.replace(day=last_day).strftime("%Y-%m-%d"),
    }


def _build_category_bars(categories):
    max_cat_total = max((row["total"] for row in categories), default=0) or 1
    bar_classes = ["", "mock-bar-2", "mock-bar-3", "mock-bar-4"]
    return [
        {
            "category": row["category"],
            "total": row["total"],
            "width_pct": round(row["total"] / max_cat_total * 100),
            "bar_class": bar_classes[index % len(bar_classes)],
        }
        for index, row in enumerate(categories)
    ]


def _load_user_spending(user_id, from_date=None, to_date=None):
    expenses = get_expenses_for_user(user_id, from_date, to_date)
    total = get_expense_total_for_user(user_id, from_date, to_date)
    categories = get_category_totals_for_user(user_id, from_date, to_date)
    return {
        "expenses": expenses,
        "total_formatted": _format_inr(total),
        "expense_count": len(expenses),
        "category_bars": _build_category_bars(categories),
    }


def _validate_expense_form():
    amount_raw = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    date_raw = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip() or None

    if not amount_raw:
        return None, "Please enter an amount."
    try:
        amount = float(amount_raw)
    except ValueError:
        return None, "Please enter a valid amount."
    if not math.isfinite(amount) or amount <= 0:
        return None, "Amount must be greater than zero."

    if not category:
        return None, "Please select a category."
    if category not in ALLOWED_CATEGORIES:
        return None, "Please select a valid category."

    if not date_raw:
        return None, "Please enter a date."
    expense_date, err = _parse_date_arg(date_raw)
    if err:
        return None, err

    if description and len(description) > MAX_EXPENSE_DESCRIPTION_LENGTH:
        return None, (
            f"Description must be {MAX_EXPENSE_DESCRIPTION_LENGTH} characters or fewer."
        )

    return {
        "amount": amount,
        "category": category,
        "date": expense_date,
        "description": description,
    }, None


def _render_landing_dashboard(user, user_id, **kwargs):
    if "filter_from_raw" in kwargs:
        raw_from = kwargs.pop("filter_from_raw")
        raw_to = kwargs.pop("filter_to_raw")
    else:
        raw_from = request.args.get("from", "").strip()
        raw_to = request.args.get("to", "").strip()

    from_date, to_date, filter_from, filter_to, filter_error = _resolve_date_filter_values(
        raw_from, raw_to
    )
    query_from = from_date
    query_to = to_date
    if filter_error:
        query_from = None
        query_to = None
    spending = _load_user_spending(user_id, query_from, query_to)

    return render_template(
        "landing.html",
        logged_in=True,
        user_name=session.get("user_name", user["name"]),
        categories=ALLOWED_CATEGORIES,
        total_formatted=spending["total_formatted"],
        expense_count=spending["expense_count"],
        expenses=spending["expenses"],
        category_bars=spending["category_bars"],
        filter_from=filter_from,
        filter_to=filter_to,
        filter_error=filter_error,
        filter_label=_build_filter_label(query_from, query_to),
        month_preset=_month_preset_bounds(),
        **kwargs,
    )


def _render_profile(user, **kwargs):
    return render_template(
        "profile.html",
        user=user,
        name=kwargs.get("name", user["name"]),
        email=kwargs.get("email", user["email"]),
        member_since=_format_member_since(user["created_at"]),
        profile_error=kwargs.get("profile_error"),
        profile_success=kwargs.get("profile_success"),
        password_error=kwargs.get("password_error"),
        password_success=kwargs.get("password_success"),
    )


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/", methods=["GET", "POST"])
def landing():
    user = _get_current_user()
    if user is None:
        if request.method == "POST":
            return redirect(url_for("login"))
        return render_template("landing.html", logged_in=False)

    user_id = user["id"]

    if request.method == "POST":
        filter_from_raw = request.form.get("from", "").strip()
        filter_to_raw = request.form.get("to", "").strip()
        expense_data, expense_error = _validate_expense_form()

        if expense_error:
            return _render_landing_dashboard(
                user,
                user_id,
                filter_from_raw=filter_from_raw,
                filter_to_raw=filter_to_raw,
                expense_error=expense_error,
                expense_amount=request.form.get("amount", "").strip(),
                expense_category=request.form.get("category", "").strip(),
                expense_date=request.form.get("date", "").strip(),
                expense_description=request.form.get("description", "").strip(),
            )

        create_expense(
            user_id,
            expense_data["amount"],
            expense_data["category"],
            expense_data["date"],
            expense_data["description"],
        )

        session["expense_success"] = "Expense added successfully."
        redirect_kwargs = {}
        if filter_from_raw:
            redirect_kwargs["from"] = filter_from_raw
        if filter_to_raw:
            redirect_kwargs["to"] = filter_to_raw
        return redirect(url_for("landing", **redirect_kwargs))

    dashboard_kwargs = {}
    expense_success = session.pop("expense_success", None)
    if expense_success:
        dashboard_kwargs["expense_success"] = expense_success
    return _render_landing_dashboard(user, user_id, **dashboard_kwargs)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    error = None
    if not name:
        error = "Please enter your full name."
    elif not _is_valid_email(email):
        error = "Please enter a valid email address."
    elif len(password) < 8:
        error = "Password must be at least 8 characters."
    elif get_user_by_email(email):
        error = "An account with this email already exists."
    else:
        create_user(name, email, generate_password_hash(password))
        return redirect(url_for("login"))

    return render_template(
        "register.html",
        error=error,
        name=name,
        email=email,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("landing"))
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = get_user_by_email(email)
    if user and check_password_hash(user["password_hash"], password):
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("landing"))

    return render_template(
        "login.html",
        error="Invalid email or password.",
        email=email,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = _get_current_user()
    if user is None:
        return redirect(url_for("login"))

    if request.method == "GET":
        return _render_profile(user)

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()

    if not name:
        return _render_profile(
            user,
            name=name,
            email=email,
            profile_error="Please enter your full name.",
        )
    if not _is_valid_email(email):
        return _render_profile(
            user,
            name=name,
            email=email,
            profile_error="Please enter a valid email address.",
        )

    existing = get_user_by_email(email)
    if existing and existing["id"] != user["id"]:
        return _render_profile(
            user,
            name=name,
            email=email,
            profile_error="An account with this email already exists.",
        )

    update_user(user["id"], name, email)
    session["user_name"] = name
    user = get_user_by_id(user["id"])
    return _render_profile(user, profile_success="Profile updated successfully.")


@app.route("/profile/password", methods=["POST"])
@login_required
def profile_password():
    user = _get_current_user()
    if user is None:
        return redirect(url_for("login"))

    current = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")

    if not check_password_hash(user["password_hash"], current):
        return _render_profile(user, password_error="Current password is incorrect.")
    if len(new_password) < 8:
        return _render_profile(
            user,
            password_error="New password must be at least 8 characters.",
        )
    if new_password != confirm:
        return _render_profile(user, password_error="New passwords do not match.")

    update_user_password(user["id"], generate_password_hash(new_password))
    user = get_user_by_id(user["id"])
    return _render_profile(user, password_success="Password updated successfully.")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)

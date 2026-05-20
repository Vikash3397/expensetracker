import os
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import (
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

@app.route("/")
def landing():
    user_id = session.get("user_id")
    if not user_id:
        return render_template("landing.html", logged_in=False)

    user = get_user_by_id(user_id)
    if user is None:
        session.clear()
        return render_template("landing.html", logged_in=False)

    expenses = get_expenses_for_user(user_id)
    total = get_expense_total_for_user(user_id)
    categories = get_category_totals_for_user(user_id)
    max_cat_total = max((row["total"] for row in categories), default=0) or 1

    bar_classes = ["", "mock-bar-2", "mock-bar-3", "mock-bar-4"]
    category_bars = []
    for index, row in enumerate(categories):
        category_bars.append(
            {
                "category": row["category"],
                "total": row["total"],
                "width_pct": round(row["total"] / max_cat_total * 100),
                "bar_class": bar_classes[index % len(bar_classes)],
            }
        )

    return render_template(
        "landing.html",
        logged_in=True,
        user_name=session.get("user_name", user["name"]),
        total_formatted=_format_inr(total),
        expense_count=len(expenses),
        expenses=expenses,
        category_bars=category_bars,
    )


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

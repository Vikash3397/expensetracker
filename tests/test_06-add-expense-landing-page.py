"""Tests for Step 06 — add expense on the landing dashboard."""

import database.db as db_module
import pytest

# ---------------------------------------------------------------------------
# Constants (spec: allowed categories and seed demo user)
# ---------------------------------------------------------------------------

ALLOWED_CATEGORIES = (
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
)

SEED_EXPENSE_COUNT = 8

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"

VALID_EXPENSE = {
    "amount": "150.25",
    "category": "Food",
    "date": "2026-05-20",
    "description": "Team lunch",
}

FILTER_FROM = "2026-05-01"
FILTER_TO = "2026-05-10"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Flask app backed by an isolated seeded SQLite database."""
    db_path = tmp_path / "expense_tracker.db"
    monkeypatch.setattr(db_module, "DATABASE", db_path)
    db_module.init_db()
    db_module.seed_db()

    from app import app as flask_app

    flask_app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "WTF_CSRF_ENABLED": False,
        }
    )
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    response = client.post(
        "/login",
        data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    assert response.status_code == 302, "Demo login should succeed"
    return client


@pytest.fixture
def demo_user_id(app):
    with app.app_context():
        user = db_module.get_user_by_email(DEMO_EMAIL)
        assert user is not None, "Seed demo user must exist"
        return user["id"]


def _expense_count(user_id):
    return len(db_module.get_expenses_for_user(user_id))


def _login(client):
    return client.post(
        "/login",
        data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )


# ---------------------------------------------------------------------------
# Auth guards (spec: unauthenticated POST redirects to login)
# ---------------------------------------------------------------------------


class TestLandingAddExpenseAuth:
    def test_post_landing_redirects_unauthenticated_to_login(self, client):
        response = client.post(
            "/",
            data=VALID_EXPENSE,
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.location

    def test_post_landing_does_not_insert_expense_when_unauthenticated(
        self, client, demo_user_id
    ):
        before = _expense_count(demo_user_id)
        client.post("/", data=VALID_EXPENSE, follow_redirects=False)
        assert _expense_count(demo_user_id) == before


# ---------------------------------------------------------------------------
# Logged-out GET — marketing page unchanged (spec definition of done #7)
# ---------------------------------------------------------------------------


class TestLoggedOutLanding:
    def test_marketing_page_has_no_dashboard_add_expense_form(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"add-expense-form" not in response.data
        assert b'name="amount"' not in response.data

    def test_marketing_page_still_shows_public_copy(self, client):
        response = client.get("/")
        assert b"Log expenses instantly" in response.data
        assert b"Start tracking free" in response.data


# ---------------------------------------------------------------------------
# Logged-in GET — add expense form (spec definition of done #1)
# ---------------------------------------------------------------------------


class TestLoggedInAddExpenseForm:
    def test_dashboard_shows_add_expense_form(self, auth_client):
        response = auth_client.get("/")
        assert response.status_code == 200
        assert b"Add expense" in response.data
        assert b'class="add-expense-form"' in response.data
        assert b'name="amount"' in response.data
        assert b'name="category"' in response.data
        assert b'name="date"' in response.data
        assert b'name="description"' in response.data

    def test_category_select_lists_all_allowed_categories(self, auth_client):
        response = auth_client.get("/")
        for category in ALLOWED_CATEGORIES:
            assert category.encode() in response.data

    def test_form_posts_to_landing_route(self, auth_client):
        response = auth_client.get("/")
        assert b'action="/"' in response.data or b"action='/'" in response.data


# ---------------------------------------------------------------------------
# Valid POST — insert and redirect (spec definition of done #2)
# ---------------------------------------------------------------------------


class TestValidAddExpense:
    def test_valid_post_inserts_expense_for_session_user(
        self, auth_client, demo_user_id
    ):
        before = _expense_count(demo_user_id)
        response = auth_client.post("/", data=VALID_EXPENSE, follow_redirects=False)
        assert response.status_code == 302
        assert _expense_count(demo_user_id) == before + 1

    def test_valid_post_redirects_without_added_query_flag(self, auth_client):
        response = auth_client.post("/", data=VALID_EXPENSE, follow_redirects=False)
        assert response.status_code == 302
        assert "added=1" not in response.location

    def test_success_message_shown_after_redirect(self, auth_client):
        response = auth_client.post("/", data=VALID_EXPENSE, follow_redirects=True)
        assert b"Expense added successfully" in response.data

    def test_success_message_not_shown_on_refresh(self, auth_client):
        auth_client.post("/", data=VALID_EXPENSE, follow_redirects=True)
        response = auth_client.get("/")
        assert b"Expense added successfully" not in response.data

    def test_new_expense_appears_in_dashboard_table(self, auth_client):
        response = auth_client.post("/", data=VALID_EXPENSE, follow_redirects=True)
        assert b"Team lunch" in response.data
        assert b"150.25" in response.data or b"150" in response.data

    def test_valid_post_without_description_succeeds(
        self, auth_client, demo_user_id
    ):
        before = _expense_count(demo_user_id)
        payload = {
            "amount": "42",
            "category": "Other",
            "date": "2026-05-21",
        }
        response = auth_client.post("/", data=payload, follow_redirects=False)
        assert response.status_code == 302
        assert _expense_count(demo_user_id) == before + 1


# ---------------------------------------------------------------------------
# Validation errors (spec definition of done #3, #4)
# ---------------------------------------------------------------------------


class TestAddExpenseValidation:
    def test_empty_amount_shows_error_and_repopulates_form(self, auth_client):
        response = auth_client.post(
            "/",
            data={"amount": "", "category": "Food", "date": "2026-05-20"},
        )
        assert response.status_code == 200
        assert b"auth-error" in response.data
        assert b"amount" in response.data.lower()

    def test_zero_amount_rejected(self, auth_client, demo_user_id):
        before = _expense_count(demo_user_id)
        response = auth_client.post(
            "/",
            data={"amount": "0", "category": "Food", "date": "2026-05-20"},
        )
        assert response.status_code == 200
        assert _expense_count(demo_user_id) == before

    def test_negative_amount_rejected(self, auth_client, demo_user_id):
        before = _expense_count(demo_user_id)
        response = auth_client.post(
            "/",
            data={"amount": "-10", "category": "Food", "date": "2026-05-20"},
        )
        assert response.status_code == 200
        assert _expense_count(demo_user_id) == before

    def test_non_numeric_amount_rejected(self, auth_client, demo_user_id):
        before = _expense_count(demo_user_id)
        response = auth_client.post(
            "/",
            data={"amount": "abc", "category": "Food", "date": "2026-05-20"},
        )
        assert response.status_code == 200
        assert _expense_count(demo_user_id) == before

    def test_nan_amount_rejected(self, auth_client, demo_user_id):
        before = _expense_count(demo_user_id)
        response = auth_client.post(
            "/",
            data={"amount": "nan", "category": "Food", "date": "2026-05-20"},
        )
        assert response.status_code == 200
        assert _expense_count(demo_user_id) == before

    def test_invalid_category_rejected_server_side(
        self, auth_client, demo_user_id
    ):
        before = _expense_count(demo_user_id)
        response = auth_client.post(
            "/",
            data={
                "amount": "10",
                "category": "Hacking",
                "date": "2026-05-20",
            },
        )
        assert response.status_code == 200
        assert _expense_count(demo_user_id) == before

    def test_missing_date_rejected(self, auth_client, demo_user_id):
        before = _expense_count(demo_user_id)
        response = auth_client.post(
            "/",
            data={"amount": "10", "category": "Food", "date": ""},
        )
        assert response.status_code == 200
        assert _expense_count(demo_user_id) == before

    def test_invalid_date_format_rejected(self, auth_client, demo_user_id):
        before = _expense_count(demo_user_id)
        response = auth_client.post(
            "/",
            data={"amount": "10", "category": "Food", "date": "20-05-2026"},
        )
        assert response.status_code == 200
        assert _expense_count(demo_user_id) == before

    def test_validation_error_repopulates_submitted_amount(self, auth_client):
        response = auth_client.post(
            "/",
            data={"amount": "12.50", "category": "Invalid", "date": "2026-05-20"},
        )
        assert b'value="12.50"' in response.data or b"12.50" in response.data

    def test_overlong_description_rejected(self, auth_client, demo_user_id):
        before = _expense_count(demo_user_id)
        response = auth_client.post(
            "/",
            data={
                "amount": "10",
                "category": "Food",
                "date": "2026-05-20",
                "description": "x" * 501,
            },
        )
        assert response.status_code == 200
        assert _expense_count(demo_user_id) == before


# ---------------------------------------------------------------------------
# Date filter preservation (spec definition of done #6)
# ---------------------------------------------------------------------------


class TestAddExpenseFilterPreservation:
    def test_success_redirect_preserves_from_and_to_params(self, auth_client):
        response = auth_client.post(
            "/",
            data={
                **VALID_EXPENSE,
                "from": FILTER_FROM,
                "to": FILTER_TO,
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert f"from={FILTER_FROM}" in response.location
        assert f"to={FILTER_TO}" in response.location
        assert "added=1" not in response.location

    def test_active_filter_hidden_fields_present_on_dashboard(self, auth_client):
        auth_client.get(f"/?from={FILTER_FROM}&to={FILTER_TO}")
        response = auth_client.get(f"/?from={FILTER_FROM}&to={FILTER_TO}")
        assert b'name="from"' in response.data
        assert FILTER_FROM.encode() in response.data
        assert FILTER_TO.encode() in response.data

    def test_validation_error_keeps_filter_on_rerender(self, auth_client):
        auth_client.get(f"/?from={FILTER_FROM}&to={FILTER_TO}")
        response = auth_client.post(
            "/",
            data={
                "amount": "0",
                "category": "Food",
                "date": "2026-05-05",
                "from": FILTER_FROM,
                "to": FILTER_TO,
            },
        )
        assert response.status_code == 200
        assert FILTER_FROM.encode() in response.data
        assert FILTER_TO.encode() in response.data


# ---------------------------------------------------------------------------
# Database helper (spec: create_expense)
# ---------------------------------------------------------------------------


class TestCreateExpenseHelper:
    def test_create_expense_inserts_row_and_returns_id(self, app, demo_user_id):
        with app.app_context():
            new_id = db_module.create_expense(
                demo_user_id,
                99.0,
                "Transport",
                "2026-05-22",
                "Bus fare",
            )
            assert new_id is not None
            expenses = db_module.get_expenses_for_user(demo_user_id)
            inserted = [row for row in expenses if row["id"] == new_id]
            assert len(inserted) == 1
            assert inserted[0]["amount"] == 99.0
            assert inserted[0]["category"] == "Transport"
            assert inserted[0]["date"] == "2026-05-22"
            assert inserted[0]["description"] == "Bus fare"

    def test_seed_still_has_expected_expense_count(self, demo_user_id):
        assert _expense_count(demo_user_id) == SEED_EXPENSE_COUNT


# ---------------------------------------------------------------------------
# Placeholder routes unchanged (spec definition of done #8)
# ---------------------------------------------------------------------------


class TestExpenseStubsUnchanged:
    def test_add_expense_route_remains_stub(self, client):
        response = client.get("/expenses/add")
        assert response.status_code == 200
        assert b"coming in Step 7" in response.data

    def test_edit_expense_route_remains_stub(self, client):
        response = client.get("/expenses/1/edit")
        assert response.status_code == 200
        assert b"coming in Step 8" in response.data

    def test_delete_expense_route_remains_stub(self, client):
        response = client.get("/expenses/1/delete")
        assert response.status_code == 200
        assert b"coming in Step 9" in response.data

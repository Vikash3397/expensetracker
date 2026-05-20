"""Tests for Step 05 — date filter and spending summary on the profile page."""

import database.db as db_module
import pytest

# ---------------------------------------------------------------------------
# Seed-derived expectations (Step 01 plan seed rows: 8 expenses, demo user)
# ---------------------------------------------------------------------------

ALL_EXPENSE_COUNT = 8
ALL_EXPENSE_TOTAL = 6302.0

FILTER_FROM = "2026-05-01"
FILTER_TO = "2026-05-10"
FILTERED_EXPENSE_COUNT = 5
FILTERED_EXPENSE_TOTAL = 3919.0

FILTERED_DESCRIPTIONS = {
    "Electricity bill",
    "Lunch at cafe",
    "Metro recharge",
    "Pharmacy",
    "Miscellaneous",
}

OUT_OF_RANGE_DESCRIPTION = "Movie tickets"

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"


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


# ---------------------------------------------------------------------------
# Auth guards
# ---------------------------------------------------------------------------


class TestProfileAuth:
    def test_profile_get_redirects_unauthenticated_to_login(self, client):
        response = client.get("/profile", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.location

    def test_profile_post_redirects_unauthenticated_to_login(self, client):
        response = client.post(
            "/profile",
            data={"name": "Hacker", "email": "hack@example.com"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.location

    def test_profile_password_post_redirects_unauthenticated_to_login(self, client):
        response = client.post(
            "/profile/password",
            data={
                "current_password": "x",
                "new_password": "newpassword1",
                "confirm_password": "newpassword1",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.location


# ---------------------------------------------------------------------------
# Profile spending section — unfiltered (definition of done #1)
# ---------------------------------------------------------------------------


class TestProfileSpendingUnfiltered:
    def test_profile_shows_spending_section_without_query_params(self, auth_client):
        response = auth_client.get("/profile")
        assert response.status_code == 200
        body = response.data
        assert b"Your spending" in body
        assert b"6,302" in body
        assert str(ALL_EXPENSE_COUNT).encode() in body
        assert b"expense-table" in body

    def test_profile_unfiltered_shows_all_seed_expenses(self, auth_client):
        response = auth_client.get("/profile")
        body = response.data
        for description in FILTERED_DESCRIPTIONS | {OUT_OF_RANGE_DESCRIPTION}:
            assert description.encode() in body

    def test_profile_unfiltered_has_date_filter_form(self, auth_client):
        response = auth_client.get("/profile")
        body = response.data
        assert b'name="from"' in body
        assert b'name="to"' in body
        assert b'method="GET"' in body
        assert b"/profile" in body
        assert b"Clear filter" in body

    def test_profile_clear_filter_link_points_to_unfiltered_profile(self, auth_client):
        response = auth_client.get("/profile")
        assert b'href="/profile"' in response.data or b"Clear filter" in response.data

    def test_profile_unfiltered_shows_category_breakdown(self, auth_client):
        """Spec: spending section shows category breakdown when categories exist."""
        response = auth_client.get("/profile")
        body = response.data
        assert b"Bills" in body
        assert b"Entertainment" in body
        assert b"dashboard-total" in body or b"data-card" in body


# ---------------------------------------------------------------------------
# Date-range filter — happy paths (definition of done #2, #5)
# ---------------------------------------------------------------------------


class TestProfileDateFilter:
    def test_profile_date_range_filters_expenses_total_and_table(
        self, auth_client
    ):
        response = auth_client.get(
            f"/profile?from={FILTER_FROM}&to={FILTER_TO}"
        )
        assert response.status_code == 200
        body = response.data
        assert b"3,919" in body
        assert str(FILTERED_EXPENSE_COUNT).encode() in body
        for description in FILTERED_DESCRIPTIONS:
            assert description.encode() in body
        assert OUT_OF_RANGE_DESCRIPTION.encode() not in body

    def test_profile_date_range_shows_active_range_label(self, auth_client):
        response = auth_client.get(
            f"/profile?from={FILTER_FROM}&to={FILTER_TO}"
        )
        assert (
            f"Showing {FILTER_FROM} to {FILTER_TO}".encode() in response.data
        )

    def test_profile_date_range_category_breakdown_matches_filtered_set(
        self, auth_client
    ):
        """Spec: filtered total and category breakdown match the filtered set."""
        response = auth_client.get(
            f"/profile?from={FILTER_FROM}&to={FILTER_TO}"
        )
        body = response.data
        assert b"2,499" in body
        assert b"450" in body
        assert b"Entertainment" not in body
        assert b"Shopping" not in body

    def test_profile_date_inputs_repopulate_after_apply(self, auth_client):
        response = auth_client.get(
            f"/profile?from={FILTER_FROM}&to={FILTER_TO}"
        )
        body = response.data
        assert f'value="{FILTER_FROM}"'.encode() in body
        assert f'value="{FILTER_TO}"'.encode() in body

    def test_profile_only_from_bound_filters_expenses(self, auth_client):
        response = auth_client.get("/profile?from=2026-05-15")
        body = response.data
        assert b"Groceries" in body
        assert b"Tea/snacks" in body
        assert b"Electricity bill" not in body

    def test_profile_only_to_bound_filters_expenses(self, auth_client):
        response = auth_client.get("/profile?to=2026-05-03")
        body = response.data
        assert b"Electricity bill" in body
        assert b"Lunch at cafe" in body
        assert b"Metro recharge" not in body

    def test_profile_clear_filter_returns_full_spending_view(self, auth_client):
        filtered = auth_client.get(
            f"/profile?from={FILTER_FROM}&to={FILTER_TO}"
        )
        assert OUT_OF_RANGE_DESCRIPTION.encode() not in filtered.data

        cleared = auth_client.get("/profile")
        assert cleared.status_code == 200
        assert b"6,302" in cleared.data
        assert OUT_OF_RANGE_DESCRIPTION.encode() in cleared.data


# ---------------------------------------------------------------------------
# Filter validation (definition of done #3)
# ---------------------------------------------------------------------------


class TestProfileFilterValidation:
    @pytest.mark.parametrize(
        "query",
        [
            "from=not-a-date",
            "to=2026-13-40",
            "from=05/01/2026",
        ],
    )
    def test_profile_invalid_date_shows_filter_error_and_unfiltered_data(
        self, auth_client, query
    ):
        response = auth_client.get(f"/profile?{query}")
        assert response.status_code == 200
        body = response.data
        assert b"auth-error" in body
        assert b"YYYY-MM-DD" in body or b"format" in body.lower()
        assert b"6,302" in body
        assert OUT_OF_RANGE_DESCRIPTION.encode() in body

    def test_profile_from_after_to_shows_filter_error_and_unfiltered_data(
        self, auth_client
    ):
        response = auth_client.get("/profile?from=2026-05-15&to=2026-05-01")
        assert response.status_code == 200
        body = response.data
        assert b"auth-error" in body or b"before" in body.lower()
        assert b"6,302" in body
        assert OUT_OF_RANGE_DESCRIPTION.encode() in body

    def test_profile_filter_error_preserves_account_forms(self, auth_client):
        response = auth_client.get("/profile?from=bad-date")
        body = response.data
        assert b"Account details" in body
        assert b"Change password" in body
        assert b"Save changes" in body
        assert b"Update password" in body


# ---------------------------------------------------------------------------
# Account forms unchanged (definition of done #6)
# ---------------------------------------------------------------------------


class TestProfileAccountForms:
    def test_profile_post_updates_account_details(self, auth_client):
        response = auth_client.post(
            "/profile",
            data={"name": "Updated Demo", "email": DEMO_EMAIL},
        )
        assert response.status_code == 200
        assert b"Profile updated successfully" in response.data
        assert b"Updated Demo" in response.data

    def test_profile_post_rejects_empty_name(self, auth_client):
        response = auth_client.post(
            "/profile",
            data={"name": "", "email": DEMO_EMAIL},
        )
        assert response.status_code == 200
        assert b"Please enter your full name" in response.data

    def test_profile_password_post_updates_password(self, auth_client):
        response = auth_client.post(
            "/profile/password",
            data={
                "current_password": DEMO_PASSWORD,
                "new_password": "newpass123",
                "confirm_password": "newpass123",
            },
        )
        assert response.status_code == 200
        assert b"Password updated successfully" in response.data

    def test_profile_password_post_rejects_wrong_current_password(
        self, auth_client
    ):
        response = auth_client.post(
            "/profile/password",
            data={
                "current_password": "wrongpassword",
                "new_password": "newpass123",
                "confirm_password": "newpass123",
            },
        )
        assert response.status_code == 200
        assert b"Current password is incorrect" in response.data

    def test_profile_post_ignores_date_query_params_per_spec(self, auth_client):
        """Spec: account POST handlers ignore date query params on re-render."""
        response = auth_client.post(
            f"/profile?from={FILTER_FROM}&to={FILTER_TO}",
            data={"name": "Filtered POST Name", "email": DEMO_EMAIL},
        )
        assert response.status_code == 200
        assert b"Profile updated successfully" in response.data
        assert b"Filtered POST Name" in response.data
        assert b"6,302" in response.data
        assert OUT_OF_RANGE_DESCRIPTION.encode() in response.data


# ---------------------------------------------------------------------------
# Landing unchanged (definition of done #8)
# ---------------------------------------------------------------------------


class TestLandingUnchanged:
    def test_landing_ignores_date_query_params_per_spec(self, auth_client):
        """Spec: date filter is profile-only; landing must show all expenses."""
        response = auth_client.get(
            f"/?from={FILTER_FROM}&to={FILTER_TO}"
        )
        assert response.status_code == 200
        assert b"6,302" in response.data
        assert OUT_OF_RANGE_DESCRIPTION.encode() in response.data
        assert str(ALL_EXPENSE_COUNT).encode() in response.data


# ---------------------------------------------------------------------------
# Database helpers — date filter side effects (spec database section)
# ---------------------------------------------------------------------------


class TestDatabaseDateFilters:
    def test_get_expenses_for_user_no_filter_returns_all(
        self, app, demo_user_id
    ):
        with app.app_context():
            expenses = db_module.get_expenses_for_user(demo_user_id)
            assert len(expenses) == ALL_EXPENSE_COUNT

    def test_get_expenses_for_user_range_returns_matching_rows(
        self, app, demo_user_id
    ):
        with app.app_context():
            expenses = db_module.get_expenses_for_user(
                demo_user_id, FILTER_FROM, FILTER_TO
            )
            assert len(expenses) == FILTERED_EXPENSE_COUNT
            dates = {row["date"] for row in expenses}
            assert min(dates) >= FILTER_FROM
            assert max(dates) <= FILTER_TO

    def test_get_expense_total_for_user_range_matches_filtered_set(
        self, app, demo_user_id
    ):
        with app.app_context():
            total = db_module.get_expense_total_for_user(
                demo_user_id, FILTER_FROM, FILTER_TO
            )
            assert total == FILTERED_EXPENSE_TOTAL

    def test_get_expense_total_for_user_no_filter_matches_all(
        self, app, demo_user_id
    ):
        with app.app_context():
            total = db_module.get_expense_total_for_user(demo_user_id)
            assert total == ALL_EXPENSE_TOTAL

    def test_get_category_totals_for_user_range_matches_filtered_set(
        self, app, demo_user_id
    ):
        with app.app_context():
            rows = db_module.get_category_totals_for_user(
                demo_user_id, FILTER_FROM, FILTER_TO
            )
            totals = {row["category"]: row["total"] for row in rows}
            assert totals["Bills"] == 2499.0
            assert totals["Food"] == 450.0
            assert "Entertainment" not in totals

    def test_get_expenses_for_user_only_from_bound(self, app, demo_user_id):
        with app.app_context():
            expenses = db_module.get_expenses_for_user(
                demo_user_id, from_date="2026-05-15"
            )
            assert len(expenses) == 2
            assert all(row["date"] >= "2026-05-15" for row in expenses)

    def test_get_expenses_for_user_only_to_bound(self, app, demo_user_id):
        with app.app_context():
            expenses = db_module.get_expenses_for_user(
                demo_user_id, to_date="2026-05-03"
            )
            assert len(expenses) == 2
            assert all(row["date"] <= "2026-05-03" for row in expenses)


# ---------------------------------------------------------------------------
# Placeholder routes unchanged (definition of done #11)
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

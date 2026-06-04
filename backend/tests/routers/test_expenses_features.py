"""
Tests for three new features added to GET /expenses:
  Feature 3 — Date Range Filtering (with proper validation)
  Feature 4 — User Isolation (each user sees only their own data)
  Feature 5 — Pagination (page + limit query params)
"""
from fastapi import status
from tests.utils import create_user_for_test, create_expense_for_test
from datetime import date


# ─────────────────────────────────────────────
#  Shared helpers
# ─────────────────────────────────────────────

def register_and_login(client, username, email, password="testpassword"):
    create_user_for_test(client, username, email, password)
    response = client.post("/login", data={"username": username, "password": password})
    return response.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ═════════════════════════════════════════════
#  FEATURE 3 — Date Range Filtering
# ═════════════════════════════════════════════

def test_date_range_reversed_dates_returns_400(client, auth_user_token):
    """
    Passing from_date AFTER to_date should return 400, not silently swap them.
    """
    response = client.get(
        "/expenses?from_date=2024-12-31&to_date=2024-01-01",
        headers=auth_headers(auth_user_token)
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "from_date" in response.json()["detail"]


def test_date_range_valid_range_filters_correctly(client, auth_user_token):
    """
    Valid date range returns only expenses within that window.
    """
    create_expense_for_test(client, auth_user_token, 50.0,  "Groceries", "inside",  date(2024, 6, 15))
    create_expense_for_test(client, auth_user_token, 100.0, "Leisure",   "outside", date(2024, 1, 1))

    response = client.get(
        "/expenses?from_date=2024-06-01&to_date=2024-06-30",
        headers=auth_headers(auth_user_token)
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["expenses"]) == 1
    assert data["expenses"][0]["category"] == "Groceries"


def test_date_range_same_start_and_end(client, auth_user_token):
    """
    from_date == to_date should work — returns expenses on exactly that day.
    """
    create_expense_for_test(client, auth_user_token, 75.0, "Health", "same-day", date(2024, 3, 20))

    response = client.get(
        "/expenses?from_date=2024-03-20&to_date=2024-03-20",
        headers=auth_headers(auth_user_token)
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["expenses"]) == 1


def test_date_range_no_filter_returns_all(client, auth_user_token):
    """
    No date params returns all expenses.
    """
    create_expense_for_test(client, auth_user_token, 10.0, "Groceries", "a", date(2024, 1, 1))
    create_expense_for_test(client, auth_user_token, 20.0, "Leisure",   "b", date(2024, 6, 1))
    create_expense_for_test(client, auth_user_token, 30.0, "Health",    "c", date(2024, 12, 1))

    response = client.get("/expenses", headers=auth_headers(auth_user_token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == 3


# ═════════════════════════════════════════════
#  FEATURE 4 — User Isolation
# ═════════════════════════════════════════════

def test_user_cannot_read_another_users_expenses(client):
    """
    User B's expense list is empty even though User A has expenses.
    """
    token_a = register_and_login(client, "userisoA", "isoa@example.com")
    token_b = register_and_login(client, "userisoB", "isob@example.com")

    create_expense_for_test(client, token_a, 100.0, "Groceries", "User A expense")

    response = client.get("/expenses", headers=auth_headers(token_b))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["expenses"] == []
    assert response.json()["total"] == 0


def test_user_cannot_update_another_users_expense(client):
    """
    User B cannot update an expense that belongs to User A — gets 404.
    """
    token_a = register_and_login(client, "isoUpdateA", "isoua@example.com")
    token_b = register_and_login(client, "isoUpdateB", "isoub@example.com")

    expense_id = create_expense_for_test(client, token_a, 100.0, "Groceries", "A's expense")["id"]

    response = client.put(
        f"/expenses/{expense_id}",
        json={"amount": 999.0},
        headers=auth_headers(token_b)
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_cannot_delete_another_users_expense(client):
    """
    User B cannot delete an expense that belongs to User A — gets 404.
    """
    token_a = register_and_login(client, "isoDelA", "isodela@example.com")
    token_b = register_and_login(client, "isoDelB", "isodelb@example.com")

    expense_id = create_expense_for_test(client, token_a, 100.0, "Groceries", "A's expense")["id"]

    response = client.delete(f"/expenses/{expense_id}", headers=auth_headers(token_b))

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_each_user_sees_only_their_own_data(client):
    """
    User A and User B both have expenses. Each sees only their own.
    """
    token_a = register_and_login(client, "ownA", "owna@example.com")
    token_b = register_and_login(client, "ownB", "ownb@example.com")

    create_expense_for_test(client, token_a, 100.0, "Groceries", "A1")
    create_expense_for_test(client, token_a, 200.0, "Health",    "A2")
    create_expense_for_test(client, token_b, 50.0,  "Leisure",   "B1")

    resp_a = client.get("/expenses", headers=auth_headers(token_a))
    resp_b = client.get("/expenses", headers=auth_headers(token_b))

    assert resp_a.json()["total"] == 2
    assert resp_b.json()["total"] == 1


# ═════════════════════════════════════════════
#  FEATURE 5 — Pagination
# ═════════════════════════════════════════════

def test_pagination_response_includes_metadata(client, auth_user_token):
    """
    Response always includes page, limit, and total keys.
    """
    response = client.get("/expenses", headers=auth_headers(auth_user_token))

    data = response.json()
    assert "expenses" in data
    assert "page" in data
    assert "limit" in data
    assert "total" in data


def test_pagination_defaults_are_page_1_limit_10(client, auth_user_token):
    """
    Without any params, defaults are page=1 and limit=10.
    """
    response = client.get("/expenses", headers=auth_headers(auth_user_token))

    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 10


def test_pagination_limit_restricts_results(client, auth_user_token):
    """
    Adding 15 expenses and requesting limit=5 gives only 5 back.
    """
    for i in range(15):
        create_expense_for_test(client, auth_user_token, 10.0 + i, "Groceries", f"expense {i}")

    response = client.get("/expenses?page=1&limit=5", headers=auth_headers(auth_user_token))

    data = response.json()
    assert len(data["expenses"]) == 5
    assert data["total"] == 15
    assert data["page"] == 1
    assert data["limit"] == 5


def test_pagination_page_2_returns_remaining(client, auth_user_token):
    """
    Page 2 with limit=10 returns the remaining 5 out of 15 total.
    """
    for i in range(15):
        create_expense_for_test(client, auth_user_token, 10.0 + i, "Health", f"expense {i}")

    response = client.get("/expenses?page=2&limit=10", headers=auth_headers(auth_user_token))

    data = response.json()
    assert len(data["expenses"]) == 5
    assert data["total"] == 15


def test_pagination_beyond_last_page_returns_empty(client, auth_user_token):
    """
    Requesting a page past the last one returns empty list, not an error.
    """
    for i in range(3):
        create_expense_for_test(client, auth_user_token, 10.0, "Groceries", f"expense {i}")

    response = client.get("/expenses?page=99&limit=10", headers=auth_headers(auth_user_token))

    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert data["expenses"] == []
    assert data["total"] == 3


def test_pagination_invalid_page_zero(client, auth_user_token):
    """
    page=0 is rejected (minimum is 1).
    """
    response = client.get("/expenses?page=0", headers=auth_headers(auth_user_token))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_pagination_invalid_limit_zero(client, auth_user_token):
    """
    limit=0 is rejected (minimum is 1).
    """
    response = client.get("/expenses?limit=0", headers=auth_headers(auth_user_token))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_pagination_limit_over_maximum(client, auth_user_token):
    """
    limit=101 is rejected (maximum is 100).
    """
    response = client.get("/expenses?limit=101", headers=auth_headers(auth_user_token))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_pagination_total_is_unaffected_by_page(client, auth_user_token):
    """
    The 'total' field reflects all matching records regardless of which page you're on.
    """
    for i in range(12):
        create_expense_for_test(client, auth_user_token, 10.0, "Utilities", f"expense {i}")

    page1 = client.get("/expenses?page=1&limit=5", headers=auth_headers(auth_user_token)).json()
    page2 = client.get("/expenses?page=2&limit=5", headers=auth_headers(auth_user_token)).json()

    assert page1["total"] == 12
    assert page2["total"] == 12

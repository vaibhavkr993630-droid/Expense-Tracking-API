from fastapi import status
from tests.utils import create_user_for_test, create_expense_for_test
from datetime import date


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def get_token(client):
    create_user_for_test(client, "analyticsuser", "analytics@example.com", "testpassword")
    response = client.post("/login", data={"username": "analyticsuser", "password": "testpassword"})
    return response.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────
#  Monthly Summary  (GET /expenses/summary/monthly)
# ─────────────────────────────────────────────

def test_monthly_summary_with_expenses(client):
    token = get_token(client)
    create_expense_for_test(client, token, 100.00, "Groceries",   "week1",  date(2024, 10, 1))
    create_expense_for_test(client, token, 200.00, "Electronics", "gadget", date(2024, 10, 15))
    create_expense_for_test(client, token, 50.00,  "Health",      "gym",    date(2024, 10, 20))

    response = client.get("/expenses/summary/monthly?month=10&year=2024", headers=auth_headers(token))

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["year"] == 2024
    assert data["month"] == 10
    assert data["expense_count"] == 3
    assert data["total_expenses"] == 350.0
    assert data["average_expense"] == 116.67


def test_monthly_summary_empty_month(client):
    token = get_token(client)

    response = client.get("/expenses/summary/monthly?month=1&year=2024", headers=auth_headers(token))

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_expenses"] == 0.0
    assert data["expense_count"] == 0
    assert data["average_expense"] == 0.0


def test_monthly_summary_ignores_other_months(client):
    token = get_token(client)
    create_expense_for_test(client, token, 100.00, "Groceries", "oct", date(2024, 10, 1))
    create_expense_for_test(client, token, 999.00, "Leisure",   "nov", date(2024, 11, 1))

    response = client.get("/expenses/summary/monthly?month=10&year=2024", headers=auth_headers(token))

    data = response.json()
    assert data["expense_count"] == 1
    assert data["total_expenses"] == 100.0


def test_monthly_summary_requires_auth(client):
    response = client.get("/expenses/summary/monthly?month=10&year=2024")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_monthly_summary_invalid_month(client):
    token = get_token(client)
    response = client.get("/expenses/summary/monthly?month=13&year=2024", headers=auth_headers(token))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ─────────────────────────────────────────────
#  Category Breakdown  (GET /expenses/summary/category)
# ─────────────────────────────────────────────

def test_category_breakdown_groups_correctly(client):
    token = get_token(client)
    create_expense_for_test(client, token, 100.00, "Groceries",   "g1", date(2024, 10, 1))
    create_expense_for_test(client, token,  50.00, "Groceries",   "g2", date(2024, 10, 5))
    create_expense_for_test(client, token, 200.00, "Electronics", "e1", date(2024, 10, 10))

    response = client.get("/expenses/summary/category", headers=auth_headers(token))

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["grand_total"] == 350.0

    categories = {c["category"]: c for c in data["categories"]}
    assert categories["Groceries"]["total"] == 150.0
    assert categories["Groceries"]["count"] == 2
    assert categories["Groceries"]["percentage"] == round(150 / 350 * 100, 2)
    assert categories["Electronics"]["total"] == 200.0


def test_category_breakdown_sorted_by_total(client):
    token = get_token(client)
    create_expense_for_test(client, token,  50.00, "Health",      "h1", date(2024, 10, 1))
    create_expense_for_test(client, token, 500.00, "Electronics", "e1", date(2024, 10, 1))
    create_expense_for_test(client, token, 100.00, "Groceries",   "g1", date(2024, 10, 1))

    response = client.get("/expenses/summary/category", headers=auth_headers(token))
    data = response.json()
    totals = [c["total"] for c in data["categories"]]
    assert totals == sorted(totals, reverse=True)


def test_category_breakdown_with_month_filter(client):
    token = get_token(client)
    create_expense_for_test(client, token, 100.00, "Groceries", "oct", date(2024, 10, 1))
    create_expense_for_test(client, token, 999.00, "Leisure",   "nov", date(2024, 11, 1))

    response = client.get("/expenses/summary/category?month=10&year=2024", headers=auth_headers(token))

    data = response.json()
    category_names = [c["category"] for c in data["categories"]]
    assert "Groceries" in category_names
    assert "Leisure" not in category_names
    assert data["grand_total"] == 100.0


def test_category_breakdown_empty(client):
    token = get_token(client)
    response = client.get("/expenses/summary/category", headers=auth_headers(token))
    data = response.json()
    assert data["grand_total"] == 0.0
    assert data["categories"] == []


def test_category_breakdown_percentages_sum_to_100(client):
    token = get_token(client)
    create_expense_for_test(client, token, 300.00, "Groceries",   "g1", date(2024, 10, 1))
    create_expense_for_test(client, token, 100.00, "Health",      "h1", date(2024, 10, 2))
    create_expense_for_test(client, token, 200.00, "Electronics", "e1", date(2024, 10, 3))

    response = client.get("/expenses/summary/category", headers=auth_headers(token))
    data = response.json()
    total_pct = sum(c["percentage"] for c in data["categories"])
    assert abs(total_pct - 100.0) < 0.1


def test_category_breakdown_requires_auth(client):
    response = client.get("/expenses/summary/category")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

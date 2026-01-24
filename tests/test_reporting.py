from datetime import date

import pytest
from fastapi.testclient import TestClient


def _create_user(client: TestClient, auth_headers: dict, name="Report Owner", email="report@example.com"):
    """Helper function to create a user for testing"""
    return client.post(
        "/api/v1/users", json={"name": name, "email": email}, headers=auth_headers
    )


def _create_account(client: TestClient, auth_headers: dict, name="Test Account", currency="USD"):
    """Helper function to create an account for testing"""
    create_payload = {
        "name": name,
        "type": "cash",
        "currency": currency,
        "initial_balance": 1000.00,
    }
    r = client.post("/api/v1/accounts", json=create_payload, headers=auth_headers)
    assert r.status_code == 200
    return r.json()


def _create_category(
    client: TestClient, auth_headers: dict, name="Test Category", category_type="expense"
):
    """Helper function to create a category for testing"""
    create_payload = {
        "name": name,
        "type": category_type,
        "color": "#FF0000",
        "icon": "shopping-cart",
    }
    r = client.post("/api/v1/categories", json=create_payload, headers=auth_headers)
    assert r.status_code in {200, 201}
    return r.json()


def _create_transaction(
    client: TestClient,
    auth_headers: dict,
    account_id: str,
    category_id: str,
    amount: str = "100.00",
    transaction_type: str = "expense",
    transaction_date: str = None,
):
    """Helper function to create a transaction for testing"""
    if transaction_date is None:
        transaction_date = date.today().isoformat()

    create_payload = {
        "account_id": account_id,
        "category_id": category_id,
        "type": transaction_type,
        "amount": amount,
        "currency": "USD",
        "date": transaction_date,
    }
    r = client.post("/api/v1/transactions", json=create_payload, headers=auth_headers)
    assert r.status_code == 200
    return r.json()


def test_categories_summary_with_valid_period_day(client, auth_headers):
    """Test that categories summary returns transaction amounts for day period"""
    _create_user(client, auth_headers)
    account = _create_account(client, auth_headers)
    category = _create_category(client, auth_headers, "Groceries", "expense")

    # Create transaction with today's date
    today = date.today().isoformat()
    _create_transaction(
        client, auth_headers, account["id"], category["id"], "150.00", "expense", today
    )

    # Get categories summary
    r = client.get(
        "/api/v1/reporting/categories-summary?period=day", headers=auth_headers
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1

    # Find our category
    cat_summary = next(
        (cat for cat in data["results"] if cat["id"] == category["id"]), None
    )
    assert cat_summary is not None
    assert "transaction_amount" in cat_summary
    assert cat_summary["transaction_amount"] == "-150.00"  # Expense is negative


def test_categories_summary_net_signed_calculation(client, auth_headers):
    """Test net-signed calculation: income adds, expense subtracts"""
    _create_user(client, auth_headers)
    account = _create_account(client, auth_headers)
    category = _create_category(client, auth_headers, "Mixed Category", "expense")

    today = date.today().isoformat()

    # Create income transaction: +100.00
    _create_transaction(
        client, auth_headers, account["id"], category["id"], "100.00", "income", today
    )

    # Create expense transaction: -30.00
    _create_transaction(
        client, auth_headers, account["id"], category["id"], "30.00", "expense", today
    )

    # Create another expense transaction: -20.00
    _create_transaction(
        client, auth_headers, account["id"], category["id"], "20.00", "expense", today
    )

    # Net should be: 100.00 - 30.00 - 20.00 = 50.00
    r = client.get(
        "/api/v1/reporting/categories-summary?period=day", headers=auth_headers
    )
    assert r.status_code == 200
    data = r.json()

    cat_summary = next(
        (cat for cat in data["results"] if cat["id"] == category["id"]), None
    )
    assert cat_summary is not None
    assert cat_summary["transaction_amount"] == "50.00"


def test_categories_summary_filter_by_type(client, auth_headers):
    """Test filtering categories by type in summary"""
    _create_user(client, auth_headers)
    account = _create_account(client, auth_headers)

    expense_cat = _create_category(client, auth_headers, "Expense Cat", "expense")
    income_cat = _create_category(client, auth_headers, "Income Cat", "income")

    today = date.today().isoformat()
    _create_transaction(
        client, auth_headers, account["id"], expense_cat["id"], "50.00", "expense", today
    )
    _create_transaction(
        client, auth_headers, account["id"], income_cat["id"], "100.00", "income", today
    )

    # Filter by expense type
    r = client.get(
        "/api/v1/reporting/categories-summary?period=day&type=expense",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert all(cat["type"] == "expense" for cat in data["results"])

    # Filter by income type
    r = client.get(
        "/api/v1/reporting/categories-summary?period=day&type=income",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert all(cat["type"] == "income" for cat in data["results"])


def test_categories_summary_invalid_period(client, auth_headers):
    """Test that invalid period is rejected"""
    _create_user(client, auth_headers)

    # Invalid period should yield 422
    r = client.get(
        "/api/v1/reporting/categories-summary?period=invalid", headers=auth_headers
    )
    assert r.status_code == 422


def test_categories_summary_missing_period(client, auth_headers):
    """Test that missing required period parameter is rejected"""
    _create_user(client, auth_headers)

    # Missing period should yield 422
    r = client.get("/api/v1/reporting/categories-summary", headers=auth_headers)
    assert r.status_code == 422


def test_categories_summary_no_transactions_returns_zero(client, auth_headers):
    """Test that categories without transactions return 0.00"""
    _create_user(client, auth_headers)
    category = _create_category(client, auth_headers, "Empty Category", "expense")

    # Get summary without creating any transactions
    r = client.get(
        "/api/v1/reporting/categories-summary?period=day", headers=auth_headers
    )
    assert r.status_code == 200
    data = r.json()

    cat_summary = next(
        (cat for cat in data["results"] if cat["id"] == category["id"]), None
    )
    assert cat_summary is not None
    assert cat_summary["transaction_amount"] == "0.00"


def test_categories_summary_income_positive(client, auth_headers):
    """Test that income transactions result in positive amounts"""
    _create_user(client, auth_headers)
    account = _create_account(client, auth_headers)
    category = _create_category(client, auth_headers, "Salary", "income")

    today = date.today().isoformat()
    _create_transaction(
        client, auth_headers, account["id"], category["id"], "2000.00", "income", today
    )

    r = client.get(
        "/api/v1/reporting/categories-summary?period=day", headers=auth_headers
    )
    assert r.status_code == 200
    data = r.json()

    cat_summary = next(
        (cat for cat in data["results"] if cat["id"] == category["id"]), None
    )
    assert cat_summary is not None
    assert cat_summary["transaction_amount"] == "2000.00"  # Positive for income


def test_categories_summary_expense_negative(client, auth_headers):
    """Test that expense transactions result in negative amounts"""
    _create_user(client, auth_headers)
    account = _create_account(client, auth_headers)
    category = _create_category(client, auth_headers, "Rent", "expense")

    today = date.today().isoformat()
    _create_transaction(
        client, auth_headers, account["id"], category["id"], "500.00", "expense", today
    )

    r = client.get(
        "/api/v1/reporting/categories-summary?period=day", headers=auth_headers
    )
    assert r.status_code == 200
    data = r.json()

    cat_summary = next(
        (cat for cat in data["results"] if cat["id"] == category["id"]), None
    )
    assert cat_summary is not None
    assert cat_summary["transaction_amount"] == "-500.00"  # Negative for expense


def test_categories_summary_all_periods(client, auth_headers):
    """Test that all period options work (day, week, month, year)"""
    _create_user(client, auth_headers)
    account = _create_account(client, auth_headers)
    category = _create_category(client, auth_headers, "Test Category", "expense")

    today = date.today().isoformat()
    _create_transaction(
        client, auth_headers, account["id"], category["id"], "10.00", "expense", today
    )

    for period in ["day", "week", "month", "year"]:
        r = client.get(
            f"/api/v1/reporting/categories-summary?period={period}",
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "results" in data
        assert isinstance(data["results"], list)

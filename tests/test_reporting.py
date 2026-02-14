from calendar import monthrange
from datetime import date

import pytest
from fastapi.testclient import TestClient


def _create_user(
    client: TestClient,
    auth_headers: dict,
    name="Report Owner",
    email="report@example.com",
    currency=None,
):
    """Helper function to create a user for testing"""
    payload = {"name": name, "email": email}
    if currency is not None:
        payload["currency"] = currency
    return client.post("/api/v1/users", json=payload, headers=auth_headers)


def _create_account(
    client: TestClient, auth_headers: dict, name="Test Account", currency="USD"
):
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
    client: TestClient,
    auth_headers: dict,
    name="Test Category",
    category_type="expense",
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
    currency: str = "USD",
    source: str = "manual",
):
    """Helper function to create a transaction for testing"""
    if transaction_date is None:
        transaction_date = date.today().isoformat()

    create_payload = {
        "account_id": account_id,
        "category_id": category_id,
        "type": transaction_type,
        "amount": amount,
        "currency": currency,
        "date": transaction_date,
        "source": source,
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
    assert "transaction_count" in cat_summary
    assert cat_summary["transaction_count"] == 1


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
    assert cat_summary["transaction_count"] == 3  # 3 transactions total


def test_categories_summary_filter_by_type(client, auth_headers):
    """Test filtering categories by type in summary"""
    _create_user(client, auth_headers)
    account = _create_account(client, auth_headers)

    expense_cat = _create_category(client, auth_headers, "Expense Cat", "expense")
    income_cat = _create_category(client, auth_headers, "Income Cat", "income")

    today = date.today().isoformat()
    _create_transaction(
        client,
        auth_headers,
        account["id"],
        expense_cat["id"],
        "50.00",
        "expense",
        today,
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


def test_categories_summary_missing_period_and_dates(client, auth_headers):
    """Test that missing both period and date range is rejected"""
    _create_user(client, auth_headers)

    # Missing both period and date range should yield 422
    r = client.get("/api/v1/reporting/categories-summary", headers=auth_headers)
    assert r.status_code == 422


def test_categories_summary_with_date_range(client, auth_headers):
    """Test that date_from and date_to can be used instead of period"""
    _create_user(client, auth_headers)
    account = _create_account(client, auth_headers)
    category = _create_category(client, auth_headers, "Date Range Cat", "expense")

    today = date.today().isoformat()
    _create_transaction(
        client, auth_headers, account["id"], category["id"], "75.00", "expense", today
    )

    # Use date range instead of period
    r = client.get(
        f"/api/v1/reporting/categories-summary?date_from={today}&date_to={today}",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    cat_summary = next(
        (cat for cat in data["results"] if cat["id"] == category["id"]), None
    )
    assert cat_summary is not None
    assert cat_summary["transaction_amount"] == "-75.00"
    assert cat_summary["transaction_count"] == 1


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
    assert cat_summary["transaction_count"] == 0


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
    assert cat_summary["transaction_count"] == 1


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
    assert cat_summary["transaction_count"] == 1


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


# -------------------------------------------------------------------------
# Balance endpoint tests (require user with currency set)
# -------------------------------------------------------------------------


def test_get_balance_total(client, auth_headers):
    """Test that /balance returns total balance in base currency"""
    _create_user(client, auth_headers, currency="USD")
    account = _create_account(client, auth_headers)
    category = _create_category(client, auth_headers, "Test", "expense")

    today = date.today().isoformat()
    _create_transaction(
        client, auth_headers, account["id"], category["id"], "50.00", "expense", today
    )

    r = client.get("/api/v1/reporting/balance", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "as_of" in data
    assert "currency" in data
    assert data["currency"] == "USD"
    assert "balance" in data
    # Initial 1000 - 50 expense = 950
    assert float(data["balance"]) == 950.0


def test_get_balance_accounts(client, auth_headers):
    """Test that /balance/accounts returns per-account balances and total"""
    _create_user(client, auth_headers, currency="USD")
    account = _create_account(client, auth_headers)
    category = _create_category(client, auth_headers, "Test", "expense")

    today = date.today().isoformat()
    _create_transaction(
        client, auth_headers, account["id"], category["id"], "25.00", "expense", today
    )

    r = client.get("/api/v1/reporting/balance/accounts", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "as_of" in data
    assert "currency" in data
    assert "accounts" in data
    assert "total" in data
    assert len(data["accounts"]) >= 1
    acc = next(a for a in data["accounts"] if a["account_id"] == account["id"])
    assert "balance_native" in acc
    assert "balance_converted" in acc
    assert "account_name" in acc


def test_get_balance_history(client, auth_headers):
    """Test that /balance/history returns points for charts"""
    _create_user(client, auth_headers, currency="USD")
    account = _create_account(client, auth_headers)
    category = _create_category(client, auth_headers, "Test", "expense")

    today = date.today().isoformat()
    _create_transaction(
        client, auth_headers, account["id"], category["id"], "10.00", "expense", today
    )

    r = client.get(
        f"/api/v1/reporting/balance/history?from={today}&to={today}&period=day",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "currency" in data
    assert "period" in data
    assert "points" in data
    assert len(data["points"]) >= 1
    assert "date" in data["points"][0]
    assert "balance" in data["points"][0]


def test_get_balance_no_currency_returns_422(client, auth_headers):
    """Test that balance endpoints return 422 when user has no currency set"""
    _create_user(client, auth_headers)  # No currency

    r = client.get("/api/v1/reporting/balance", headers=auth_headers)
    assert r.status_code == 422
    assert "currency" in r.json().get("detail", "").lower()


# -------------------------------------------------------------------------
# Query count tests (N+1 safety: balance endpoints must use O(1) queries)
# -------------------------------------------------------------------------


def test_balance_total_query_count(client, auth_headers, query_counter):
    """GET /balance must use O(1) queries: <=12 regardless of account count."""
    _create_user(client, auth_headers, currency="USD")
    _create_account(client, auth_headers, "A1", "USD")
    _create_account(client, auth_headers, "A2", "USD")
    _create_account(client, auth_headers, "A3", "USD")

    query_counter[0] = 0
    r = client.get("/api/v1/reporting/balance", headers=auth_headers)
    assert r.status_code == 200
    assert query_counter[0] <= 12, (
        f"Expected <= 12 queries (O(1)), got {query_counter[0]}. "
        "Balance endpoints must be N+1 safe."
    )


def test_balance_accounts_query_count(client, auth_headers, query_counter):
    """GET /balance/accounts must use O(1) queries: <=12 regardless of account count."""
    _create_user(client, auth_headers, currency="USD")
    _create_account(client, auth_headers, "A1", "USD")
    _create_account(client, auth_headers, "A2", "USD")

    query_counter[0] = 0
    r = client.get("/api/v1/reporting/balance/accounts", headers=auth_headers)
    assert r.status_code == 200
    assert query_counter[0] <= 12, (
        f"Expected <= 12 queries (O(1)), got {query_counter[0]}. "
        "Balance accounts endpoint must be N+1 safe."
    )


def test_balance_history_query_count(client, auth_headers, query_counter):
    """GET /balance/history must use O(1) queries regardless of date range size."""
    _create_user(client, auth_headers, currency="USD")
    account = _create_account(client, auth_headers)
    category = _create_category(client, auth_headers, "Test", "expense")
    _create_transaction(
        client,
        auth_headers,
        account["id"],
        category["id"],
        "10.00",
        "expense",
        "2025-12-01",
    )

    query_counter[0] = 0
    r = client.get(
        "/api/v1/reporting/balance/history?from=2025-12-01&to=2025-12-31&period=day",
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert query_counter[0] <= 15, (
        f"Expected <= 15 queries (O(1)), got {query_counter[0]}. "
        "Balance history must not scale with number of days."
    )


# -------------------------------------------------------------------------
# Cashflow history endpoint tests
# -------------------------------------------------------------------------


def test_cashflow_history_monthly_continuous_series(client, auth_headers):
    _create_user(client, auth_headers, currency="USD")
    account = _create_account(client, auth_headers, currency="USD")
    category = _create_category(client, auth_headers, "CFH Expense", "expense")
    salary = _create_category(client, auth_headers, "CFH Salary", "income")

    _create_transaction(
        client,
        auth_headers,
        account["id"],
        category["id"],
        "100.00",
        "expense",
        "2025-01-10",
    )
    _create_transaction(
        client,
        auth_headers,
        account["id"],
        salary["id"],
        "300.00",
        "income",
        "2025-03-10",
    )

    r = client.get(
        "/api/v1/reporting/cashflow/history"
        "?date_from=2025-01-01&date_to=2025-03-31&period=month&currency=USD",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["period"] == "month"
    assert data["currency"] == "USD"
    assert len(data["points"]) == 3
    assert [p["period_start"] for p in data["points"]] == [
        "2025-01-01",
        "2025-02-01",
        "2025-03-01",
    ]
    feb = data["points"][1]
    assert feb["income"] == "0.00"
    assert feb["expense"] == "0.00"
    assert feb["net"] == "0.00"


@pytest.mark.parametrize(
    "period,date_from,date_to,expected_points",
    [
        ("day", "2026-01-01", "2026-01-03", 3),
        ("week", "2026-01-01", "2026-01-10", 2),
        ("month", "2026-01-01", "2026-03-31", 3),
        ("year", "2025-01-01", "2026-12-31", 2),
    ],
)
def test_cashflow_history_day_week_month_year_periods(
    client,
    auth_headers,
    period,
    date_from,
    date_to,
    expected_points,
):
    _create_user(client, auth_headers, currency="USD")
    account = _create_account(client, auth_headers, currency="USD")
    category = _create_category(client, auth_headers, "Granularity Cat", "expense")
    _create_transaction(
        client,
        auth_headers,
        account["id"],
        category["id"],
        "20.00",
        "expense",
        "2026-01-02",
    )

    r = client.get(
        f"/api/v1/reporting/cashflow/history?date_from={date_from}&date_to={date_to}&period={period}&currency=USD",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["period"] == period
    assert len(data["points"]) == expected_points
    assert [p["period_start"] for p in data["points"]] == sorted(
        [p["period_start"] for p in data["points"]]
    )


def test_cashflow_history_filters_and_logic(client, auth_headers):
    _create_user(client, auth_headers, currency="USD")
    account_a = _create_account(client, auth_headers, name="A", currency="USD")
    account_b = _create_account(client, auth_headers, name="B", currency="USD")
    category_a = _create_category(client, auth_headers, "Food", "expense")
    category_b = _create_category(client, auth_headers, "Travel", "expense")

    _create_transaction(
        client,
        auth_headers,
        account_a["id"],
        category_a["id"],
        "80.00",
        "expense",
        "2026-01-05",
        source="manual",
    )
    _create_transaction(
        client,
        auth_headers,
        account_a["id"],
        category_a["id"],
        "20.00",
        "expense",
        "2026-01-06",
        source="imported",
    )
    _create_transaction(
        client,
        auth_headers,
        account_b["id"],
        category_b["id"],
        "100.00",
        "expense",
        "2026-01-07",
        source="manual",
    )

    r = client.get(
        "/api/v1/reporting/cashflow/history"
        f"?date_from=2026-01-01&date_to=2026-01-31&period=month"
        f"&account_id={account_a['id']}&category_id={category_a['id']}"
        "&amount_min=70&amount_max=90&source=manual&currency=USD",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["points"]) == 1
    point = data["points"][0]
    assert point["income"] == "0.00"
    assert point["expense"] == "80.00"
    assert point["net"] == "-80.00"


def test_cashflow_history_expense_sign_and_net_formula(client, auth_headers):
    _create_user(client, auth_headers, currency="USD")
    account = _create_account(client, auth_headers, currency="USD")
    income_category = _create_category(client, auth_headers, "Payroll", "income")
    expense_category = _create_category(client, auth_headers, "Bills", "expense")

    _create_transaction(
        client,
        auth_headers,
        account["id"],
        income_category["id"],
        "200.00",
        "income",
        "2026-01-10",
    )
    _create_transaction(
        client,
        auth_headers,
        account["id"],
        expense_category["id"],
        "75.00",
        "expense",
        "2026-01-10",
    )

    r = client.get(
        "/api/v1/reporting/cashflow/history"
        "?date_from=2026-01-01&date_to=2026-01-31&period=month&currency=USD",
        headers=auth_headers,
    )
    assert r.status_code == 200
    point = r.json()["points"][0]
    assert float(point["expense"]) >= 0
    assert float(point["net"]) == float(point["income"]) - float(point["expense"])


def test_cashflow_history_currency_explicit_no_conversion(client, auth_headers):
    _create_user(client, auth_headers, currency="USD")
    usd_account = _create_account(client, auth_headers, name="USD Acc", currency="USD")
    eur_account = _create_account(client, auth_headers, name="EUR Acc", currency="EUR")
    income_category = _create_category(client, auth_headers, "Income", "income")

    _create_transaction(
        client,
        auth_headers,
        usd_account["id"],
        income_category["id"],
        "100.00",
        "income",
        "2026-01-12",
        currency="USD",
    )
    _create_transaction(
        client,
        auth_headers,
        eur_account["id"],
        income_category["id"],
        "10.00",
        "income",
        "2026-01-12",
        currency="EUR",
    )

    r = client.get(
        "/api/v1/reporting/cashflow/history"
        "?date_from=2026-01-01&date_to=2026-01-31&period=month&currency=USD",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["currency"] == "USD"
    assert data["points"][0]["income"] == "100.00"


def test_cashflow_history_without_currency_converts_to_base(client, auth_headers):
    _create_user(client, auth_headers, currency="USD")
    usd_account = _create_account(client, auth_headers, name="USD Acc", currency="USD")
    eur_account = _create_account(client, auth_headers, name="EUR Acc", currency="EUR")
    income_category = _create_category(client, auth_headers, "Income", "income")

    _create_transaction(
        client,
        auth_headers,
        usd_account["id"],
        income_category["id"],
        "100.00",
        "income",
        "2026-01-12",
        currency="USD",
    )
    _create_transaction(
        client,
        auth_headers,
        eur_account["id"],
        income_category["id"],
        "10.00",
        "income",
        "2026-01-12",
        currency="EUR",
    )

    r = client.get(
        "/api/v1/reporting/cashflow/history"
        "?date_from=2026-01-01&date_to=2026-01-31&period=month",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["currency"] == "USD"
    # 100 USD + (10 EUR * 0.90 EUR->USD conversion) = 109.00
    assert data["points"][0]["income"] == "109.00"


def test_cashflow_history_invalid_date_range_returns_422(client, auth_headers):
    _create_user(client, auth_headers, currency="USD")
    r = client.get(
        "/api/v1/reporting/cashflow/history"
        "?date_from=2026-02-01&date_to=2026-01-01&period=month",
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_cashflow_history_invalid_amount_range_returns_422(client, auth_headers):
    _create_user(client, auth_headers, currency="USD")
    r = client.get(
        "/api/v1/reporting/cashflow/history"
        "?date_from=2026-01-01&date_to=2026-02-01&period=month&amount_min=20&amount_max=10",
        headers=auth_headers,
    )
    assert r.status_code == 422


# -------------------------------------------------------------------------
# Period Comparison tests
# -------------------------------------------------------------------------


def test_calculate_previous_equivalent_period():
    """Unit test for date_helper.calculate_previous_equivalent_period."""
    from datetime import date

    from app.shared.helpers.date_helper import calculate_previous_equivalent_period

    # 90-day range
    prev_start, prev_end = calculate_previous_equivalent_period(
        date(2026, 4, 1), date(2026, 6, 29)
    )
    assert prev_end == date(2026, 3, 31)
    assert (date(2026, 6, 29) - date(2026, 4, 1)).days == (prev_end - prev_start).days

    # One week
    prev_start, prev_end = calculate_previous_equivalent_period(
        date(2026, 2, 9), date(2026, 2, 15)
    )
    assert prev_end == date(2026, 2, 8)
    assert prev_start == date(2026, 2, 2)


def test_period_comparison_requires_auth(client):
    """Period comparison returns 401 without auth."""
    r = client.get("/api/v1/reporting/period-comparison?period=month")
    assert r.status_code == 401


def test_period_comparison_invalid_params_returns_422(client, auth_headers):
    """Invalid params: date_from > date_to, period null with one date."""
    _create_user(client, auth_headers)
    r = client.get(
        "/api/v1/reporting/period-comparison"
        "?date_from=2026-02-01&date_to=2026-01-01",
        headers=auth_headers,
    )
    assert r.status_code == 422

    r2 = client.get(
        "/api/v1/reporting/period-comparison?date_from=2026-01-01",
        headers=auth_headers,
    )
    assert r2.status_code == 422


def test_period_comparison_with_period_month(client, auth_headers):
    """Happy path: period=month compares current month vs previous."""
    _create_user(client, auth_headers, currency="USD")
    account = _create_account(client, auth_headers, currency="USD")
    category = _create_category(client, auth_headers, "Food", "expense")

    r = client.get(
        "/api/v1/reporting/period-comparison?period=month",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "current_period" in data
    assert "previous_period" in data
    assert "summary" in data
    assert "start" in data["current_period"]
    assert "end" in data["current_period"]
    assert "income" in data["current_period"]
    assert "expense" in data["current_period"]
    assert "net" in data["current_period"]
    assert "difference" in data["summary"]
    assert "percentage_change" in data["summary"]
    assert "percentage_change_available" in data["summary"]
    assert data["summary"]["trend"] in ("up", "down", "flat")


def test_period_comparison_with_date_range(client, auth_headers):
    """Happy path: date_from/date_to for custom range."""
    _create_user(client, auth_headers, currency="USD")
    account = _create_account(client, auth_headers, currency="USD")
    category = _create_category(client, auth_headers, "Food", "expense")
    _create_transaction(
        client,
        auth_headers,
        account["id"],
        category["id"],
        "50.00",
        "expense",
        "2026-01-15",
    )

    r = client.get(
        "/api/v1/reporting/period-comparison"
        "?date_from=2026-01-01&date_to=2026-01-31",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["current_period"]["start"] == "2026-01-01"
    assert data["current_period"]["end"] == "2026-01-31"
    assert data["previous_period"]["end"] == "2025-12-31"
    assert data["current_period"]["expense"] == "50.00"


def test_period_comparison_previous_net_zero(client, auth_headers):
    """When previous.net=0, percentage_change is null and percentage_change_available false."""
    _create_user(client, auth_headers, currency="USD")
    account = _create_account(client, auth_headers, currency="USD")
    category = _create_category(client, auth_headers, "Salary", "income")

    today = date.today()
    _, last_day = monthrange(today.year, today.month)
    current_start = date(today.year, today.month, 1)
    current_end = date(today.year, today.month, last_day)

    _create_transaction(
        client,
        auth_headers,
        account["id"],
        category["id"],
        "100.00",
        "income",
        today.isoformat(),
    )

    r = client.get(
        "/api/v1/reporting/period-comparison"
        f"?date_from={current_start}&date_to={current_end}",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["previous_period"]["net"] == "0.00"
    assert data["summary"]["percentage_change"] is None
    assert data["summary"]["percentage_change_available"] is False


def test_period_comparison_trend_up(client, auth_headers):
    """Trend is up when current net > previous net."""
    _create_user(client, auth_headers, currency="USD")
    account = _create_account(client, auth_headers, currency="USD")
    category = _create_category(client, auth_headers, "Salary", "income")

    _create_transaction(
        client,
        auth_headers,
        account["id"],
        category["id"],
        "50.00",
        "income",
        "2025-12-15",
    )
    _create_transaction(
        client,
        auth_headers,
        account["id"],
        category["id"],
        "150.00",
        "income",
        "2026-01-15",
    )

    r = client.get(
        "/api/v1/reporting/period-comparison"
        "?date_from=2026-01-01&date_to=2026-01-31",
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["summary"]["trend"] == "up"

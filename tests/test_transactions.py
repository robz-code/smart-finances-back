import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient


def _create_user(
    client: TestClient,
    auth_headers: dict,
    name="Transaction Owner",
    email="owner@example.com",
):
    """Helper function to create a user for testing"""
    return client.post(
        "/api/v1/users", json={"name": name, "email": email}, headers=auth_headers
    )


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


def _create_category(client: TestClient, auth_headers: dict, name="Test Category"):
    """Helper function to create a category for testing"""
    create_payload = {
        "name": name,
        "type": "expense",
        "color": "#FF0000",
        "icon": "shopping-cart",
    }
    r = client.post("/api/v1/categories", json=create_payload, headers=auth_headers)
    assert r.status_code in {200, 201}
    return r.json()


def _create_tag(client: TestClient, auth_headers: dict, name="Test Tag"):
    """Helper function to create a tag for testing"""
    create_payload = {
        "name": name,
        "color": "#00FF00",
    }
    r = client.post("/api/v1/tags", json=create_payload, headers=auth_headers)
    assert r.status_code == 201
    return r.json()


def _create_transaction(
    client: TestClient,
    auth_headers: dict,
    account_id: str,
    amount: str = "100.00",
    transaction_type: str = "expense",
    category_id: str | None = None,
    transaction_date: str = "2024-01-15",
    tag: dict | None = None,
):
    """Helper function to create a transaction for testing"""
    if category_id is None:
        category = _create_category(client, auth_headers)
        category_id = category["id"]

    create_payload = {
        "account_id": account_id,
        "category_id": category_id,
        "type": transaction_type,
        "amount": amount,
        "currency": "USD",
        "date": transaction_date,
        "source": "manual",
        "has_debt": False,
    }
    if tag:
        create_payload["tag"] = tag
    r = client.post("/api/v1/transactions", json=create_payload, headers=auth_headers)
    assert r.status_code == 200
    return r.json()


class TestTransactionCRUD:
    """Test CRUD operations for transactions"""

    def test_transactions_crud_flow(self, client: TestClient, auth_headers: dict):
        """Test complete CRUD flow for transactions"""
        # Ensure a current user exists
        r = _create_user(client, auth_headers)
        assert r.status_code == 200

        # Create account
        account = _create_account(client, auth_headers)
        account_id = account["id"]

        # Create category
        category = _create_category(client, auth_headers)
        category_id = category["id"]

        # Create transaction
        create_payload = {
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "150.50",
            "currency": "USD",
            "date": "2024-01-15",
            "source": "manual",
            "has_debt": False,
        }
        r = client.post(
            "/api/v1/transactions", json=create_payload, headers=auth_headers
        )
        assert r.status_code == 200
        transaction = r.json()
        transaction_id = transaction["id"]

        # Verify created transaction
        assert "account_id" not in transaction
        assert transaction["account"]["id"] == account["id"]
        assert transaction["account"]["name"] == account["name"]
        assert "category_id" not in transaction
        assert transaction["category"]["id"] == category["id"]
        assert transaction["category"]["name"] == category["name"]
        assert transaction["type"] == "expense"
        assert transaction["amount"] == "150.50"
        assert transaction["currency"] == "USD"
        assert transaction["date"] == "2024-01-15"
        assert transaction["source"] == "manual"
        assert transaction["has_installments"] is False
        assert transaction["has_debt"] is False
        assert transaction["tag"] is None
        assert "id" in transaction
        assert "user_id" in transaction
        assert "created_at" in transaction

        # Read transaction details
        r = client.get(f"/api/v1/transactions/{transaction_id}", headers=auth_headers)
        assert r.status_code == 200
        retrieved = r.json()
        assert retrieved["id"] == transaction_id
        assert retrieved["amount"] == "150.50"
        assert retrieved["account"]["name"] == account["name"]
        assert retrieved["category"]["name"] == category["name"]
        assert retrieved["has_debt"] is False
        assert retrieved["tag"] is None

        # Update transaction
        update_payload = {
            "amount": "200.00",
            "type": "income",
        }
        r = client.put(
            f"/api/v1/transactions/{transaction_id}",
            json=update_payload,
            headers=auth_headers,
        )
        assert r.status_code == 200
        updated = r.json()
        assert updated["amount"] == "200.00"
        assert updated["type"] == "income"
        # Verify other fields remain unchanged
        assert updated["account"]["name"] == account["name"]
        assert updated["category"]["name"] == category["name"]
        assert updated["has_debt"] is False

        # Delete transaction
        r = client.delete(
            f"/api/v1/transactions/{transaction_id}", headers=auth_headers
        )
        assert r.status_code == 204

        # Verify deletion
        r = client.get(f"/api/v1/transactions/{transaction_id}", headers=auth_headers)
        assert r.status_code == 404

    def test_create_transaction_minimal_data(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating transaction with minimal required data"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)

        create_payload = {
            "account_id": account["id"],
            "category_id": category["id"],
            "type": "expense",
            "amount": "50.00",
            "date": "2024-01-15",
        }
        r = client.post(
            "/api/v1/transactions", json=create_payload, headers=auth_headers
        )
        assert r.status_code == 200

        transaction = r.json()
        assert transaction["account"]["name"] == account["name"]
        assert transaction["category"]["name"] == category["name"]
        assert transaction["type"] == "expense"
        assert transaction["amount"] == "50.00"
        assert transaction["date"] == "2024-01-15"
        assert transaction["source"] == "manual"  # default value
        assert transaction["has_installments"] is False  # default value
        assert transaction["has_debt"] is False  # default value
        assert transaction["tag"] is None

    def test_create_transaction_with_all_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating transaction with all optional fields"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)
        tag_payload = {
            "name": "High Priority",
            "color": "#FF00FF",
        }

        create_payload = {
            "account_id": account["id"],
            "category_id": category["id"],
            "type": "income",
            "amount": "1000.00",
            "currency": "EUR",
            "date": "2024-01-20",
            "source": "bank_transfer",
            "has_debt": True,
            "installments": [
                {"due_date": "2024-02-20", "amount": "500.00"},
                {"due_date": "2024-03-20", "amount": "500.00"},
            ],
            "tag": tag_payload,
        }
        r = client.post(
            "/api/v1/transactions", json=create_payload, headers=auth_headers
        )
        assert r.status_code == 200

        transaction = r.json()
        assert transaction["account"]["name"] == account["name"]
        assert transaction["category"]["name"] == category["name"]
        assert transaction["type"] == "income"
        assert transaction["amount"] == "1000.00"
        assert transaction["currency"] == "EUR"
        assert transaction["source"] == "bank_transfer"
        assert transaction["has_installments"] is True
        assert transaction["has_debt"] is True
        assert transaction["tag"]["name"] == tag_payload["name"]
        assert "id" in transaction["tag"]

        tags_response = client.get("/api/v1/tags", headers=auth_headers)
        assert tags_response.status_code == 200
        tags_payload = tags_response.json()
        assert any(
            tag["name"] == tag_payload["name"] for tag in tags_payload["results"]
        )

    def test_create_transaction_with_existing_tag(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating a transaction referencing an existing tag"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)
        tag = _create_tag(client, auth_headers, name="Recurring")

        transaction = _create_transaction(
            client,
            auth_headers,
            account_id=account["id"],
            category_id=category["id"],
            tag={"id": tag["id"], "name": tag["name"]},
        )

        assert transaction["tag"]["id"] == tag["id"]
        assert transaction["tag"]["name"] == tag["name"]

    def test_create_transaction_invalid_account(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating transaction with non-existent account"""
        _create_user(client, auth_headers)
        category = _create_category(client, auth_headers)

        create_payload = {
            "account_id": str(uuid.uuid4()),  # Non-existent account
            "type": "expense",
            "amount": "100.00",
            "date": "2024-01-15",
            "category_id": category["id"],
        }
        r = client.post(
            "/api/v1/transactions", json=create_payload, headers=auth_headers
        )
        assert r.status_code == 403  # Access denied

    def test_create_transaction_zero_amount(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating transaction with zero amount (should fail)"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)

        create_payload = {
            "account_id": account["id"],
            "type": "expense",
            "amount": "0.00",
            "date": "2024-01-15",
            "category_id": category["id"],
        }
        r = client.post(
            "/api/v1/transactions", json=create_payload, headers=auth_headers
        )
        assert r.status_code == 400  # Bad request

    def test_update_transaction_partial(self, client: TestClient, auth_headers: dict):
        """Test updating transaction with partial data"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        transaction = _create_transaction(client, auth_headers, account["id"])

        # Update only amount
        update_payload = {"amount": "75.25"}
        r = client.put(
            f"/api/v1/transactions/{transaction['id']}",
            json=update_payload,
            headers=auth_headers,
        )
        assert r.status_code == 200

        updated = r.json()
        assert updated["amount"] == "75.25"
        # Verify other fields remain unchanged
        assert updated["type"] == "expense"
        assert updated["account"]["name"] == account["name"]

    def test_update_transaction_not_found(self, client: TestClient, auth_headers: dict):
        """Test updating non-existent transaction"""
        _create_user(client, auth_headers)

        update_payload = {"amount": "100.00"}
        r = client.put(
            f"/api/v1/transactions/{uuid.uuid4()}",
            json=update_payload,
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_delete_transaction_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent transaction"""
        _create_user(client, auth_headers)

        r = client.delete(f"/api/v1/transactions/{uuid.uuid4()}", headers=auth_headers)
        assert r.status_code == 404


class TestTransactionSearch:
    """Test transaction search functionality"""

    def test_search_transactions_basic(self, client: TestClient, auth_headers: dict):
        """Test basic transaction search"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)

        # Create multiple transactions
        _create_transaction(
            client, auth_headers, account["id"], "100.00", "expense", None, "2024-01-15"
        )
        _create_transaction(
            client, auth_headers, account["id"], "200.00", "income", None, "2024-01-16"
        )
        _create_transaction(
            client, auth_headers, account["id"], "150.00", "expense", None, "2024-01-17"
        )

        # Search all transactions
        r = client.get("/api/v1/transactions", headers=auth_headers)
        assert r.status_code == 200

        result = r.json()
        assert result["total"] >= 3
        assert len(result["results"]) >= 3

    def test_search_transactions_by_account(
        self, client: TestClient, auth_headers: dict
    ):
        """Test searching transactions by account"""
        _create_user(client, auth_headers)
        account1 = _create_account(client, auth_headers, "Account 1", "USD")
        account2 = _create_account(client, auth_headers, "Account 2", "EUR")

        # Create transactions in different accounts
        _create_transaction(
            client,
            auth_headers,
            account1["id"],
            "100.00",
            "expense",
            None,
            "2024-01-15",
        )
        _create_transaction(
            client, auth_headers, account2["id"], "200.00", "income", None, "2024-01-16"
        )

        # Search by account 1
        r = client.get(
            f"/api/v1/transactions?account_id={account1['id']}", headers=auth_headers
        )
        assert r.status_code == 200

        result = r.json()
        assert result["total"] >= 1
        assert all(
            t["account"]["name"] == account1["name"] and "account_id" not in t
            for t in result["results"]
        )

    def test_search_transactions_by_type(self, client: TestClient, auth_headers: dict):
        """Test searching transactions by type"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)

        # Create transactions of different types
        _create_transaction(
            client, auth_headers, account["id"], "100.00", "expense", None, "2024-01-15"
        )
        _create_transaction(
            client, auth_headers, account["id"], "200.00", "income", None, "2024-01-16"
        )
        _create_transaction(
            client, auth_headers, account["id"], "150.00", "expense", None, "2024-01-17"
        )

        # Search by expense type
        r = client.get("/api/v1/transactions?type=expense", headers=auth_headers)
        assert r.status_code == 200

        result = r.json()
        assert result["total"] >= 2
        assert all(t["type"] == "expense" for t in result["results"])

    def test_search_transactions_by_date_range(
        self, client: TestClient, auth_headers: dict
    ):
        """Test searching transactions by date range"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)

        # Create transactions on different dates
        _create_transaction(
            client, auth_headers, account["id"], "100.00", "expense", None, "2024-01-15"
        )
        _create_transaction(
            client, auth_headers, account["id"], "200.00", "income", None, "2024-01-20"
        )
        _create_transaction(
            client, auth_headers, account["id"], "150.00", "expense", None, "2024-02-01"
        )

        # Search by date range
        r = client.get(
            "/api/v1/transactions?date_from=2024-01-15&date_to=2024-01-31",
            headers=auth_headers,
        )
        assert r.status_code == 200

        result = r.json()
        assert result["total"] >= 2
        # Verify dates are within range
        for transaction in result["results"]:
            transaction_date = date.fromisoformat(transaction["date"])
            assert date(2024, 1, 15) <= transaction_date <= date(2024, 1, 31)

    def test_search_transactions_by_amount_range(
        self, client: TestClient, auth_headers: dict
    ):
        """Test searching transactions by amount range"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)

        # Create transactions with different amounts
        _create_transaction(
            client, auth_headers, account["id"], "50.00", "expense", None, "2024-01-15"
        )
        _create_transaction(
            client, auth_headers, account["id"], "150.00", "income", None, "2024-01-16"
        )
        _create_transaction(
            client, auth_headers, account["id"], "300.00", "expense", None, "2024-01-17"
        )

        # Search by amount range
        r = client.get(
            "/api/v1/transactions?amount_min=100.00&amount_max=200.00",
            headers=auth_headers,
        )
        assert r.status_code == 200

        result = r.json()
        assert result["total"] >= 1
        # Verify amounts are within range
        for transaction in result["results"]:
            amount = Decimal(transaction["amount"])
            assert Decimal("100.00") <= amount <= Decimal("200.00")

    def test_search_transactions_multiple_filters(
        self, client: TestClient, auth_headers: dict
    ):
        """Test searching transactions with multiple filters"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)

        # Create transactions with different characteristics
        _create_transaction(
            client,
            auth_headers,
            account["id"],
            "100.00",
            "expense",
            category["id"],
            "2024-01-15",
        )
        _create_transaction(
            client, auth_headers, account["id"], "200.00", "income", None, "2024-01-16"
        )
        _create_transaction(
            client,
            auth_headers,
            account["id"],
            "150.00",
            "expense",
            category["id"],
            "2024-01-17",
        )

        # Search with multiple filters
        r = client.get(
            f"/api/v1/transactions?type=expense&category_id={category['id']}&amount_min=50.00",
            headers=auth_headers,
        )
        assert r.status_code == 200

        result = r.json()
        assert result["total"] >= 2
        # Verify all filters are applied
        for transaction in result["results"]:
            assert transaction["type"] == "expense"
            assert transaction["category"]["name"] == category["name"]
            assert "category_id" not in transaction
            assert Decimal(transaction["amount"]) >= Decimal("50.00")


class TestTransactionConvenienceEndpoints:
    """Test convenience endpoints for transactions"""

    def test_get_transactions_by_account(self, client: TestClient, auth_headers: dict):
        """Test getting transactions by account endpoint"""
        _create_user(client, auth_headers)
        account1 = _create_account(client, auth_headers, "Account 1", "USD")
        account2 = _create_account(client, auth_headers, "Account 2", "EUR")

        # Create transactions in different accounts
        _create_transaction(
            client,
            auth_headers,
            account1["id"],
            "100.00",
            "expense",
            None,
            "2024-01-15",
        )
        _create_transaction(
            client, auth_headers, account2["id"], "200.00", "income", None, "2024-01-16"
        )

        # Get transactions by account 1
        r = client.get(
            f"/api/v1/transactions/account/{account1['id']}", headers=auth_headers
        )
        assert r.status_code == 200

        result = r.json()
        assert result["total"] >= 1
        assert all(
            t["account"]["name"] == account1["name"] and "account_id" not in t
            for t in result["results"]
        )

    def test_get_transactions_by_category(self, client: TestClient, auth_headers: dict):
        """Test getting transactions by category endpoint"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        category1 = _create_category(client, auth_headers, "Category 1")
        category2 = _create_category(client, auth_headers, "Category 2")

        # Create transactions in different categories
        _create_transaction(
            client,
            auth_headers,
            account["id"],
            "100.00",
            "expense",
            category1["id"],
            "2024-01-15",
        )
        _create_transaction(
            client,
            auth_headers,
            account["id"],
            "200.00",
            "income",
            category2["id"],
            "2024-01-16",
        )

        # Get transactions by category 1
        r = client.get(
            f"/api/v1/transactions/category/{category1['id']}", headers=auth_headers
        )
        assert r.status_code == 200

        result = r.json()
        assert result["total"] >= 1
        assert all(
            t["category"]["name"] == category1["name"] and "category_id" not in t
            for t in result["results"]
        )

    def test_get_transactions_by_group(self, client: TestClient, auth_headers: dict):
        """Test getting transactions by group endpoint"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)

        # Create a transaction (group_id is optional, so we'll test without it)
        transaction = _create_transaction(
            client, auth_headers, account["id"], "100.00", "expense", None, "2024-01-15"
        )

        # Test the endpoint (should work even without group_id)
        r = client.get(
            f"/api/v1/transactions/group/{uuid.uuid4()}", headers=auth_headers
        )
        assert r.status_code == 200

        result = r.json()
        # Should return empty results for non-existent group
        assert result["total"] == 0


class TestTransactionValidation:
    """Test transaction validation and error cases"""

    def test_create_transaction_missing_required_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating transaction with missing required fields"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)

        # Missing account_id
        create_payload = {
            "type": "expense",
            "amount": "100.00",
            "date": "2024-01-15",
            "category_id": category["id"],
        }
        r = client.post(
            "/api/v1/transactions", json=create_payload, headers=auth_headers
        )
        assert r.status_code == 422  # Validation error

        # Missing type
        create_payload = {
            "account_id": account["id"],
            "amount": "100.00",
            "date": "2024-01-15",
            "category_id": category["id"],
        }
        r = client.post(
            "/api/v1/transactions", json=create_payload, headers=auth_headers
        )
        assert r.status_code == 422  # Validation error

        # Missing amount
        create_payload = {
            "account_id": account["id"],
            "type": "expense",
            "date": "2024-01-15",
            "category_id": category["id"],
        }
        r = client.post(
            "/api/v1/transactions", json=create_payload, headers=auth_headers
        )
        assert r.status_code == 422  # Validation error

        # Missing date
        create_payload = {
            "account_id": account["id"],
            "type": "expense",
            "amount": "100.00",
            "category_id": category["id"],
        }
        r = client.post(
            "/api/v1/transactions", json=create_payload, headers=auth_headers
        )
        assert r.status_code == 422  # Validation error

    def test_create_transaction_invalid_uuid(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating transaction with invalid UUID format"""
        _create_user(client, auth_headers)
        category = _create_category(client, auth_headers)

        create_payload = {
            "account_id": "invalid-uuid",
            "type": "expense",
            "amount": "100.00",
            "date": "2024-01-15",
            "category_id": category["id"],
        }
        r = client.post(
            "/api/v1/transactions", json=create_payload, headers=auth_headers
        )
        assert r.status_code == 422  # Validation error

    def test_create_transaction_invalid_date_format(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating transaction with invalid date format"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)

        create_payload = {
            "account_id": account["id"],
            "type": "expense",
            "amount": "100.00",
            "date": "invalid-date",
            "category_id": category["id"],
        }
        r = client.post(
            "/api/v1/transactions", json=create_payload, headers=auth_headers
        )
        assert r.status_code == 422  # Validation error

    def test_create_transaction_invalid_amount_format(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating transaction with invalid amount format"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)

        create_payload = {
            "account_id": account["id"],
            "type": "expense",
            "amount": "invalid-amount",
            "date": "2024-01-15",
            "category_id": category["id"],
        }
        r = client.post(
            "/api/v1/transactions", json=create_payload, headers=auth_headers
        )
        assert r.status_code == 422  # Validation error

    def test_unauthorized_access(self, client: TestClient):
        """Test accessing transactions without authentication"""
        # Try to create transaction without auth
        create_payload = {
            "account_id": str(uuid.uuid4()),
            "type": "expense",
            "amount": "100.00",
            "date": "2024-01-15",
            "category_id": str(uuid.uuid4()),
        }
        r = client.post("/api/v1/transactions", json=create_payload)
        assert r.status_code == 401  # Unauthorized

        # Try to get transactions without auth
        r = client.get("/api/v1/transactions")
        assert r.status_code == 401  # Unauthorized

        # Try to get specific transaction without auth
        r = client.get(f"/api/v1/transactions/{uuid.uuid4()}")
        assert r.status_code == 401  # Unauthorized

    def test_create_transaction_invalid_type(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating transaction with invalid type"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)

        create_payload = {
            "account_id": account["id"],
            "type": "transfer",
            "amount": "100.00",
            "date": "2024-01-15",
            "category_id": category["id"],
        }
        r = client.post(
            "/api/v1/transactions", json=create_payload, headers=auth_headers
        )
        assert r.status_code == 400  # Bad request

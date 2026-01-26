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


def _create_concept(client: TestClient, auth_headers: dict, name="Test Concept"):
    """Helper function to create a concept for testing"""
    create_payload = {
        "name": name,
        "color": "#00FF00",
    }
    r = client.post("/api/v1/concept", json=create_payload, headers=auth_headers)
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
    concept: dict | None = None,
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
    }
    if concept:
        create_payload["concept"] = concept
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
        assert transaction["concept"] is None
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
        assert retrieved["concept"] is None

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
        assert transaction["concept"] is None

    def test_create_transaction_with_all_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating transaction with all optional fields"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)
        concept_payload = {
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
            "concept": concept_payload,
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
        assert transaction["concept"]["name"] == concept_payload["name"]
        assert "id" in transaction["concept"]

        concepts_response = client.get("/api/v1/concept", headers=auth_headers)
        assert concepts_response.status_code == 200
        concepts_payload = concepts_response.json()
        assert any(
            concept["name"] == concept_payload["name"]
            for concept in concepts_payload["results"]
        )

    def test_create_transaction_with_existing_concept(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating a transaction referencing an existing concept"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)
        concept = _create_concept(client, auth_headers, name="Recurring")

        transaction = _create_transaction(
            client,
            auth_headers,
            account_id=account["id"],
            category_id=category["id"],
            concept={"id": concept["id"], "name": concept["name"]},
        )

        assert transaction["concept"]["id"] == concept["id"]
        assert transaction["concept"]["name"] == concept["name"]

    def test_create_transaction_with_existing_concept_id_only(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating a transaction referencing an existing concept by ID only (no name)"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)
        concept = _create_concept(client, auth_headers, name="Work Expense")

        # Reference concept by ID only, without providing name
        transaction = _create_transaction(
            client,
            auth_headers,
            account_id=account["id"],
            category_id=category["id"],
            concept={"id": concept["id"]},
        )

        assert transaction["concept"]["id"] == concept["id"]
        assert transaction["concept"]["name"] == concept["name"]
        assert transaction["concept"]["name"] == "Work Expense"

    def test_create_transaction_creates_new_concept(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating a transaction with a new concept (concept is created automatically)"""
        _create_user(client, auth_headers)
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)

        # Create transaction with concept name and color - concept should be created automatically
        transaction = _create_transaction(
            client,
            auth_headers,
            account_id=account["id"],
            category_id=category["id"],
            concept={"name": "Personal", "color": "#FF5733"},
        )

        assert transaction["concept"] is not None
        assert transaction["concept"]["name"] == "Personal"
        assert "id" in transaction["concept"]

        # Verify the concept was actually created and can be retrieved with all fields
        concepts_response = client.get("/api/v1/concept", headers=auth_headers)
        assert concepts_response.status_code == 200
        concepts_payload = concepts_response.json()
        created_concept = next(
            (
                concept
                for concept in concepts_payload["results"]
                if concept["name"] == "Personal"
            ),
            None,
        )
        assert created_concept is not None
        assert created_concept["name"] == "Personal"
        assert created_concept["color"] == "#FF5733"
        assert created_concept["id"] == transaction["concept"]["id"]

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

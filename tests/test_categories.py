import os
import uuid

import jwt
from fastapi.testclient import TestClient


def ensure_user(client, auth_headers):
    r = client.post(
        "/api/v1/users",
        json={"name": "Cat Owner", "email": "cat@example.com"},
        headers=auth_headers,
    )
    assert r.status_code == 200


def test_categories_crud_flow(client, auth_headers):
    ensure_user(client, auth_headers)

    # Create
    payload = {"name": "Food", "icon": "🍔", "color": "#ff0000"}
    r = client.post("/api/v1/categories", json=payload, headers=auth_headers)
    assert r.status_code == 201
    cat = r.json()
    cat_id = cat["id"]
    assert cat["name"] == "Food"

    # List
    r = client.get("/api/v1/categories", headers=auth_headers)
    assert r.status_code == 200
    lst = r.json()
    assert lst["total"] >= 1

    # Read one
    r = client.get(f"/api/v1/categories/{cat_id}", headers=auth_headers)
    assert r.status_code == 200
    one = r.json()
    assert one["id"] == cat_id

    # Update
    r = client.put(
        f"/api/v1/categories/{cat_id}", json={"name": "Groceries"}, headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Groceries"

    # Delete
    r = client.delete(f"/api/v1/categories/{cat_id}", headers=auth_headers)
    assert r.status_code == 204


def test_categories_filter_by_type(client, auth_headers):
    ensure_user(client, auth_headers)

    # Create an expense category (default)
    r = client.post(
        "/api/v1/categories",
        json={"name": "Groceries", "icon": "🛒", "color": "#00ff00"},
        headers=auth_headers,
    )
    assert r.status_code == 201

    # Create an income category
    r = client.post(
        "/api/v1/categories",
        json={"name": "Salary", "type": "income", "icon": "💰", "color": "#0000ff"},
        headers=auth_headers,
    )
    assert r.status_code == 201

    # Filter by income type
    r = client.get("/api/v1/categories?type=income", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert all(cat["type"] == "income" for cat in data["results"])


def test_category_type_defaults_and_override(client, auth_headers):
    ensure_user(client, auth_headers)

    # Create without explicit type -> should default to expense
    r = client.post(
        "/api/v1/categories",
        json={"name": "Default Expense", "icon": "🧾", "color": "#CCCCCC"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    cat_default = r.json()
    assert cat_default["type"] == "expense"

    # Create with explicit income type
    r = client.post(
        "/api/v1/categories",
        json={"name": "Salary", "type": "income", "icon": "💰", "color": "#00FF00"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    cat_income = r.json()
    assert cat_income["type"] == "income"


def test_category_invalid_type_rejected(client, auth_headers):
    ensure_user(client, auth_headers)

    # Invalid type should be rejected by Pydantic/Enum validation
    r = client.post(
        "/api/v1/categories",
        json={"name": "Invalid", "type": "invalid_type", "color": "#000000"},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_categories_filter_invalid_type_query(client, auth_headers):
    ensure_user(client, auth_headers)

    # Invalid enum value in query param should yield 422
    r = client.get("/api/v1/categories?type=invalid_type", headers=auth_headers)
    assert r.status_code == 422


class TestCategoryDeleteGuardAndMigrate:
    """Tests for category deletion guard (409) and /migrate endpoint."""

    def _ensure_user(self, client: TestClient, auth_headers: dict) -> None:
        r = client.post(
            "/api/v1/users",
            json={"name": "Cat Guard User", "email": "catguard@example.com"},
            headers=auth_headers,
        )
        assert r.status_code == 200

    def _create_account(self, client: TestClient, auth_headers: dict) -> dict:
        r = client.post(
            "/api/v1/accounts",
            json={
                "name": "Guard Account",
                "type": "cash",
                "currency": "USD",
                "initial_balance": 1000.00,
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        return r.json()

    def _create_category(
        self,
        client: TestClient,
        auth_headers: dict,
        name: str = "Source Category",
        cat_type: str = "expense",
    ) -> dict:
        r = client.post(
            "/api/v1/categories",
            json={"name": name, "type": cat_type, "color": "#FF0000"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        return r.json()

    def _create_transaction(
        self,
        client: TestClient,
        auth_headers: dict,
        account_id: str,
        category_id: str,
    ) -> dict:
        r = client.post(
            "/api/v1/transactions",
            json={
                "account_id": account_id,
                "category_id": category_id,
                "type": "expense",
                "amount": "50.00",
                "currency": "USD",
                "date": "2024-01-15",
            },
            headers=auth_headers,
        )
        assert r.status_code in {200, 201}
        return r.json()

    def test_delete_category_with_transactions_returns_409(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        self._ensure_user(client, auth_headers)
        account = self._create_account(client, auth_headers)
        category = self._create_category(client, auth_headers)
        self._create_transaction(client, auth_headers, account["id"], category["id"])

        r = client.delete(
            f"/api/v1/categories/{category['id']}", headers=auth_headers
        )
        assert r.status_code == 409
        detail = r.json()["detail"]
        assert "transaction" in detail.lower()

    def test_migrate_then_delete_category_succeeds(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        self._ensure_user(client, auth_headers)
        account = self._create_account(client, auth_headers)
        source = self._create_category(client, auth_headers, name="Old Category")
        target = self._create_category(client, auth_headers, name="New Category")
        self._create_transaction(client, auth_headers, account["id"], source["id"])

        # Before migrate: delete blocked with 409
        r = client.delete(f"/api/v1/categories/{source['id']}", headers=auth_headers)
        assert r.status_code == 409

        # Migrate transactions to target
        r = client.post(
            f"/api/v1/categories/{source['id']}/migrate",
            json={"target_category_id": target["id"]},
            headers=auth_headers,
        )
        assert r.status_code == 204

        # After migrate: delete now succeeds
        r = client.delete(f"/api/v1/categories/{source['id']}", headers=auth_headers)
        assert r.status_code == 204

    def test_migrate_category_wrong_type_returns_422(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        self._ensure_user(client, auth_headers)
        expense_cat = self._create_category(
            client, auth_headers, name="Expense Cat", cat_type="expense"
        )
        income_cat = self._create_category(
            client, auth_headers, name="Income Cat", cat_type="income"
        )

        r = client.post(
            f"/api/v1/categories/{expense_cat['id']}/migrate",
            json={"target_category_id": income_cat["id"]},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_migrate_category_not_owned_returns_403(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Second user cannot migrate FROM a category they don't own."""
        self._ensure_user(client, auth_headers)
        source = self._create_category(client, auth_headers, name="User A Category")

        # Create second user with their own category
        other_user_id = uuid.uuid4()
        other_token = jwt.encode(
            {"sub": str(other_user_id)},
            os.environ["JWT_SECRET_KEY"],
            algorithm="HS256",
        )
        other_headers = {"Authorization": f"Bearer {other_token}"}
        client.post(
            "/api/v1/users",
            json={"name": "Other User", "email": "other403a@example.com"},
            headers=other_headers,
        )
        target = self._create_category(client, other_headers, name="User B Category")

        # Other user tries to migrate from User A's source — should be 403
        r = client.post(
            f"/api/v1/categories/{source['id']}/migrate",
            json={"target_category_id": target["id"]},
            headers=other_headers,
        )
        assert r.status_code == 403

    def test_migrate_target_not_owned_returns_403(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Cannot migrate to a category owned by a different user."""
        self._ensure_user(client, auth_headers)
        source = self._create_category(client, auth_headers, name="My Source")

        # Create target owned by a different user
        other_user_id = uuid.uuid4()
        other_token = jwt.encode(
            {"sub": str(other_user_id)},
            os.environ["JWT_SECRET_KEY"],
            algorithm="HS256",
        )
        other_headers = {"Authorization": f"Bearer {other_token}"}
        client.post(
            "/api/v1/users",
            json={"name": "Other User 2", "email": "other403b@example.com"},
            headers=other_headers,
        )
        other_target = self._create_category(client, other_headers, name="Other Target")

        # First user tries to migrate to a category they don't own — 403
        r = client.post(
            f"/api/v1/categories/{source['id']}/migrate",
            json={"target_category_id": other_target["id"]},
            headers=auth_headers,
        )
        assert r.status_code == 403

    def test_delete_empty_category_returns_204(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        self._ensure_user(client, auth_headers)
        category = self._create_category(client, auth_headers, name="Empty Cat")

        r = client.delete(
            f"/api/v1/categories/{category['id']}", headers=auth_headers
        )
        assert r.status_code == 204

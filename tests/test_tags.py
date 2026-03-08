"""
Phase 7: Tag hard delete verification.

Tags already have the correct cascade setup:
  - `cascade="all, delete-orphan"` on the ORM relationship (Transaction →
    transaction_tags)
  - `ON DELETE CASCADE` on `transaction_tags.tag_id` FK

These tests verify that:
1. Deleting a tag removes all its `transaction_tags` associations.
2. Deleting a tag that belongs to a different user raises 403.
3. Deleting one tag on a transaction leaves the other tags intact.
"""

import os
import uuid

import jwt
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_other_headers() -> dict:
    """Return Authorization headers for a freshly-generated user UUID."""
    other_user_id = uuid.uuid4()
    token = jwt.encode(
        {"sub": str(other_user_id)},
        os.environ["JWT_SECRET_KEY"],
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _ensure_user(client: TestClient, auth_headers: dict, email: str) -> None:
    r = client.post(
        "/api/v1/users",
        json={"name": "Tag Test User", "email": email},
        headers=auth_headers,
    )
    assert r.status_code == 200


def _create_account(client: TestClient, auth_headers: dict) -> dict:
    r = client.post(
        "/api/v1/accounts",
        json={
            "name": "Tag Test Account",
            "type": "cash",
            "currency": "USD",
            "initial_balance": 1000.00,
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    return r.json()


def _create_category(client: TestClient, auth_headers: dict) -> dict:
    r = client.post(
        "/api/v1/categories",
        json={"name": "Tag Category", "type": "expense", "color": "#123456"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    return r.json()


def _create_tag(
    client: TestClient, auth_headers: dict, name: str = "test-tag"
) -> dict:
    r = client.post(
        "/api/v1/tags",
        json={"name": name, "color": "#AABBCC"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    return r.json()


def _create_transaction_with_tags(
    client: TestClient,
    auth_headers: dict,
    account_id: str,
    category_id: str,
    tag_names: list[str],
) -> dict:
    """Create a transaction and inline-attach tags by name."""
    r = client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "30.00",
            "currency": "USD",
            "date": "2024-02-01",
            "tags": [{"name": n, "color": "#CCCCCC"} for n in tag_names],
        },
        headers=auth_headers,
    )
    assert r.status_code in {200, 201}
    return r.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTagHardDeleteCascade:
    """Tag deletion should cascade and remove transaction_tag associations."""

    def test_delete_tag_removes_transaction_tag_associations(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Deleting a tag removes its junction rows; the transaction remains."""
        _ensure_user(client, auth_headers, "tag-cascade@example.com")
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)

        # Create transaction with one inline tag
        tx = _create_transaction_with_tags(
            client, auth_headers, account["id"], category["id"], ["removable-tag"]
        )
        assert len(tx["tags"]) == 1
        tag_id = tx["tags"][0]["id"]

        # Verify the tag exists
        r = client.get(f"/api/v1/tags/{tag_id}", headers=auth_headers)
        assert r.status_code == 200

        # Delete the tag
        r = client.delete(f"/api/v1/tags/{tag_id}", headers=auth_headers)
        assert r.status_code == 204

        # Tag must be gone
        r = client.get(f"/api/v1/tags/{tag_id}", headers=auth_headers)
        assert r.status_code == 404

        # Transaction still exists but its tags list is now empty
        r = client.get(f"/api/v1/transactions/{tx['id']}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["tags"] == []

    def test_delete_tag_not_owned_returns_403(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """A user cannot delete a tag they don't own."""
        _ensure_user(client, auth_headers, "tag-owner403@example.com")
        owned_tag = _create_tag(client, auth_headers, name="my-private-tag")

        # Second user tries to delete first user's tag
        other_headers = _make_other_headers()
        client.post(
            "/api/v1/users",
            json={"name": "Sneaky User", "email": "sneaky@example.com"},
            headers=other_headers,
        )

        r = client.delete(
            f"/api/v1/tags/{owned_tag['id']}", headers=other_headers
        )
        assert r.status_code == 403

    def test_tag_associations_preserved_on_transaction_after_other_tag_deleted(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Deleting tag A does not affect tag B on the same transaction."""
        _ensure_user(client, auth_headers, "tag-preserve@example.com")
        account = _create_account(client, auth_headers)
        category = _create_category(client, auth_headers)

        # Create transaction with two inline tags
        tx = _create_transaction_with_tags(
            client,
            auth_headers,
            account["id"],
            category["id"],
            ["tag-alpha", "tag-beta"],
        )
        assert len(tx["tags"]) == 2

        # Identify the two tags
        tag_alpha = next(t for t in tx["tags"] if t["name"] == "tag-alpha")
        tag_beta = next(t for t in tx["tags"] if t["name"] == "tag-beta")

        # Delete only tag-alpha
        r = client.delete(f"/api/v1/tags/{tag_alpha['id']}", headers=auth_headers)
        assert r.status_code == 204

        # Transaction should still have tag-beta and only tag-beta
        r = client.get(f"/api/v1/transactions/{tx['id']}", headers=auth_headers)
        assert r.status_code == 200
        remaining_ids = [t["id"] for t in r.json()["tags"]]
        assert tag_alpha["id"] not in remaining_ids
        assert tag_beta["id"] in remaining_ids

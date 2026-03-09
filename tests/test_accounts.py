import datetime
import os
import uuid

import jwt
import pytest
from fastapi.testclient import TestClient


def _create_user(client, auth_headers, name="Acc Owner", email="owner@example.com"):
    return client.post(
        "/api/v1/users", json={"name": name, "email": email}, headers=auth_headers
    )


def test_accounts_crud_flow(client, auth_headers):
    # Ensure a current user exists
    r = _create_user(client, auth_headers)
    assert r.status_code == 200

    # Create account
    create_payload = {
        "name": "Main Wallet",
        "type": "cash",
        "currency": "MXN",
        "initial_balance": 100.5,
        "color": "#336699",
    }
    r = client.post("/api/v1/accounts", json=create_payload, headers=auth_headers)
    assert r.status_code == 200
    acc = r.json()
    acc_id = acc["id"]
    assert acc["name"] == "Main Wallet"
    assert acc["color"] == "#336699"

    # Read list
    r = client.get("/api/v1/accounts", headers=auth_headers)
    assert r.status_code == 200
    lst = r.json()
    assert lst["total"] >= 1
    assert any(item["id"] == acc_id for item in lst["results"])

    # Read one
    r = client.get(f"/api/v1/accounts/{acc_id}", headers=auth_headers)
    assert r.status_code == 200
    one = r.json()
    assert one["id"] == acc_id
    assert one["color"] == "#336699"

    # Update
    update_payload = {"name": "Updated Wallet", "color": "#112233"}
    r = client.put(
        f"/api/v1/accounts/{acc_id}", json=update_payload, headers=auth_headers
    )
    assert r.status_code == 200
    updated = r.json()
    assert updated["name"] == "Updated Wallet"
    assert updated["color"] == "#112233"

    # Delete
    r = client.delete(f"/api/v1/accounts/{acc_id}", headers=auth_headers)
    assert r.status_code == 204


# ---------------------------------------------------------------------------
# Phase 3 — Soft Delete tests
# ---------------------------------------------------------------------------


class TestAccountSoftDelete:
    """Verify soft-delete behaviour: account hidden, transactions retained."""

    def _make_user_and_account(
        self,
        client,
        auth_headers,
        name="SoftOwner",
        email="soft@example.com",
        acc_name="Soft Account",
    ):
        r = client.post(
            "/api/v1/users", json={"name": name, "email": email}, headers=auth_headers
        )
        assert r.status_code == 200
        r = client.post(
            "/api/v1/accounts",
            json={
                "name": acc_name,
                "type": "cash",
                "currency": "USD",
                "initial_balance": 0,
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        return r.json()["id"]

    def test_soft_delete_account_returns_204(self, client, auth_headers):
        acc_id = self._make_user_and_account(client, auth_headers)
        r = client.delete(f"/api/v1/accounts/{acc_id}", headers=auth_headers)
        assert r.status_code == 204

    def test_get_deleted_account_returns_404(self, client, auth_headers):
        acc_id = self._make_user_and_account(client, auth_headers)
        r = client.delete(f"/api/v1/accounts/{acc_id}", headers=auth_headers)
        assert r.status_code == 204

        r = client.get(f"/api/v1/accounts/{acc_id}", headers=auth_headers)
        assert r.status_code == 404

    def test_list_excludes_deleted_account(self, client, auth_headers):
        acc_id = self._make_user_and_account(client, auth_headers)

        # Verify account appears in list before deletion
        r = client.get("/api/v1/accounts", headers=auth_headers)
        assert r.status_code == 200
        ids_before = [a["id"] for a in r.json()["results"]]
        assert acc_id in ids_before

        # Soft-delete
        r = client.delete(f"/api/v1/accounts/{acc_id}", headers=auth_headers)
        assert r.status_code == 204

        # Verify account is absent from list
        r = client.get("/api/v1/accounts", headers=auth_headers)
        assert r.status_code == 200
        ids_after = [a["id"] for a in r.json()["results"]]
        assert acc_id not in ids_after

    def test_delete_account_removes_snapshots(
        self, client, auth_headers, db_session_factory
    ):
        """Snapshots for the account are purged when account is soft-deleted."""
        from app.entities.account import Account
        from app.entities.balance_snapshot import BalanceSnapshot
        from app.entities.user import User

        acc_id = self._make_user_and_account(client, auth_headers)
        acc_uuid = uuid.UUID(acc_id)

        # Insert a snapshot directly into DB
        db = db_session_factory()
        try:
            snap = BalanceSnapshot(
                id=uuid.uuid4(),
                account_id=acc_uuid,
                currency="USD",
                snapshot_date=datetime.date(2026, 1, 1),
                balance=500,
            )
            db.add(snap)
            db.commit()
            snap_id = snap.id

            # Verify snapshot exists
            found = (
                db.query(BalanceSnapshot).filter(BalanceSnapshot.id == snap_id).first()
            )
            assert found is not None
        finally:
            db.close()

        # Soft-delete via API
        r = client.delete(f"/api/v1/accounts/{acc_id}", headers=auth_headers)
        assert r.status_code == 204

        # Verify snapshot is gone
        db2 = db_session_factory()
        try:
            found = (
                db2.query(BalanceSnapshot).filter(BalanceSnapshot.id == snap_id).first()
            )
            assert (
                found is None
            ), "Snapshot should have been deleted on account soft-delete"
        finally:
            db2.close()

    def test_delete_account_forbidden_if_not_owner(self, client):
        """A user cannot delete an account owned by another user."""
        # Create two separate users with their own JWT tokens
        user_a_id = uuid.uuid4()
        user_b_id = uuid.uuid4()
        secret = os.environ["JWT_SECRET_KEY"]

        headers_a = {
            "Authorization": f"Bearer {jwt.encode({'sub': str(user_a_id)}, secret, algorithm='HS256')}"
        }
        headers_b = {
            "Authorization": f"Bearer {jwt.encode({'sub': str(user_b_id)}, secret, algorithm='HS256')}"
        }

        # Register user A and create an account
        r = client.post(
            "/api/v1/users",
            json={"name": "User A", "email": "a@example.com"},
            headers=headers_a,
        )
        assert r.status_code == 200
        r = client.post(
            "/api/v1/accounts",
            json={
                "name": "A Account",
                "type": "cash",
                "currency": "USD",
                "initial_balance": 0,
            },
            headers=headers_a,
        )
        assert r.status_code == 200
        acc_id = r.json()["id"]

        # Register user B
        r = client.post(
            "/api/v1/users",
            json={"name": "User B", "email": "b@example.com"},
            headers=headers_b,
        )
        assert r.status_code == 200

        # User B tries to delete user A's account → 403
        r = client.delete(f"/api/v1/accounts/{acc_id}", headers=headers_b)
        assert r.status_code == 403

        # Account still visible to owner A
        r = client.get(f"/api/v1/accounts/{acc_id}", headers=headers_a)
        assert r.status_code == 200

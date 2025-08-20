from uuid import uuid4
from datetime import datetime
import uuid as _uuid


def ensure_primary_user(client, auth_headers):
    unique_email = f"primary+{_uuid.uuid4().hex}@example.com"
    r = client.post("/api/v1/users", json={"name": "Primary", "email": unique_email}, headers=auth_headers)
    assert r.status_code == 200


def test_create_contact_when_user_exists(client, auth_headers):
    ensure_primary_user(client, auth_headers)

    # Create a second user directly via the API using a different token
    # We need a second token with different user_id to simulate existing user
    import os, jwt
    second_token = jwt.encode({"sub": str(uuid4())}, os.environ["JWT_SECRET_KEY"], algorithm="HS256")
    headers2 = {"Authorization": f"Bearer {second_token}"}
    r = client.post("/api/v1/users", json={"name": "Alice", "email": "alice@example.com"}, headers=headers2)
    assert r.status_code == 200
    existing_user = r.json()

    # Now, with the primary user's token, add Alice as contact
    payload = {"name": "Alice", "email": "alice@example.com"}
    r = client.post("/api/v1/contacts", json=payload, headers=auth_headers)
    assert r.status_code == 200
    detail = r.json()
    assert detail["id"] == existing_user["id"]
    assert detail["is_registered"] is True


def test_create_contact_when_user_not_exists(client, auth_headers):
    ensure_primary_user(client, auth_headers)
    payload = {"name": "Bob", "email": "bob@example.com"}
    r = client.post("/api/v1/contacts", json=payload, headers=auth_headers)
    assert r.status_code == 200
    detail = r.json()
    assert detail["email"] == "bob@example.com"
    assert detail["is_registered"] is False


def test_get_contacts_and_detail(client, auth_headers):
    ensure_primary_user(client, auth_headers)

    # Create contact user via separate token
    import os, jwt
    contact_token = jwt.encode({"sub": str(uuid4())}, os.environ["JWT_SECRET_KEY"], algorithm="HS256")
    headers_contact = {"Authorization": f"Bearer {contact_token}"}
    r = client.post("/api/v1/users", json={"name": "Charlie", "email": "charlie@example.com"}, headers=headers_contact)
    assert r.status_code == 200
    contact_user = r.json()

    # Link as contact using primary token
    r = client.post("/api/v1/contacts", json={"name": "Charlie", "email": "charlie@example.com"}, headers=auth_headers)
    assert r.status_code == 200

    # List contacts
    r = client.get("/api/v1/contacts/", headers=auth_headers)
    assert r.status_code == 200
    contacts = r.json()
    assert any(c["email"] == "charlie@example.com" for c in contacts)

    # Detail (no debts expected)
    r = client.get(f"/api/v1/contacts/{contact_user['id']}", headers=auth_headers)
    assert r.status_code == 200
    detail = r.json()
    assert detail["contact"]["id"] == contact_user["id"]
    assert isinstance(detail["debts"], list)


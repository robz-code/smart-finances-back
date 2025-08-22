import uuid


def test_create_user_and_get_me_flow(client, auth_headers):
    # Create
    import uuid as _uuid

    payload = {
        "name": "John Doe",
        "email": f"john+{_uuid.uuid4().hex}@example.com",
        "phone_number": "+12345678901",
        "currency": "USD",
        "language": "en",
        "profile_image": "https://example.com/avatar.png",
    }
    r = client.post("/api/v1/users", json=payload, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == payload["email"]
    assert body["is_registered"] is True
    assert body["name"] == payload["name"]

    # Get me
    r = client.get("/api/v1/users/", headers=auth_headers)
    assert r.status_code == 200
    me = r.json()
    assert me["id"] == body["id"]
    assert me["email"] == payload["email"]


def test_update_user(client, auth_headers):
    # First create user
    import uuid as _uuid

    payload = {
        "name": "Jane Smith",
        "email": f"jane+{_uuid.uuid4().hex}@example.com",
        "phone_number": "+19876543210",
        "currency": "EUR",
        "language": "en",
    }
    r = client.post("/api/v1/users", json=payload, headers=auth_headers)
    assert r.status_code == 200

    # Update
    update_payload = {
        "name": "Jane S",
        "email": "jane@example.com",
        "phone_number": "+19876543210",
        "currency": "EUR",
        "language": "es",
        "is_registered": True,
    }
    r = client.put("/api/v1/users/", json=update_payload, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Jane S"
    assert body["language"] == "es"


def test_delete_user(client, auth_headers):
    import uuid as _uuid

    payload = {"name": "Del User", "email": f"del+{_uuid.uuid4().hex}@example.com"}
    r = client.post("/api/v1/users", json=payload, headers=auth_headers)
    assert r.status_code == 200

    r = client.delete("/api/v1/users/", headers=auth_headers)
    assert r.status_code == 204

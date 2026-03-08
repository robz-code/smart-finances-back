def ensure_user(client, auth_headers):
    r = client.post(
        "/api/v1/users",
        json={"name": "Concept Owner", "email": "concept@example.com"},
        headers=auth_headers,
    )
    assert r.status_code == 200


def _create_account(client, auth_headers):
    r = client.post(
        "/api/v1/accounts",
        json={"name": "Test Account", "type": "cash", "currency": "USD", "initial_balance": 500},
        headers=auth_headers,
    )
    assert r.status_code == 200
    return r.json()


def _create_category(client, auth_headers):
    r = client.post(
        "/api/v1/categories",
        json={"name": "Test Cat", "type": "expense"},
        headers=auth_headers,
    )
    assert r.status_code in {200, 201}
    return r.json()


def test_concepts_crud_flow(client, auth_headers):
    ensure_user(client, auth_headers)

    # Create
    payload = {"name": "urgent", "color": "#ff0"}
    r = client.post("/api/v1/concept/", json=payload, headers=auth_headers)
    assert r.status_code == 201
    concept = r.json()
    concept_id = concept["id"]
    assert concept["name"] == "urgent"

    # List
    r = client.get("/api/v1/concept/", headers=auth_headers)
    assert r.status_code == 200
    lst = r.json()
    assert lst["total"] >= 1

    # Read one
    r = client.get(f"/api/v1/concept/{concept_id}", headers=auth_headers)
    assert r.status_code == 200
    one = r.json()
    assert one["id"] == concept_id

    # Update
    r = client.put(
        f"/api/v1/concept/{concept_id}",
        json={"name": "important"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["name"] == "important"

    # Delete
    r = client.delete(f"/api/v1/concept/{concept_id}", headers=auth_headers)
    assert r.status_code == 204


def test_delete_concept_nullifies_transaction_concept_id(client, auth_headers):
    """Deleting a concept sets concept_id to NULL on linked transactions (ON DELETE SET NULL)."""
    ensure_user(client, auth_headers)

    # Set up account and category
    account = _create_account(client, auth_headers)
    category = _create_category(client, auth_headers)

    # Create a concept
    r = client.post(
        "/api/v1/concept/",
        json={"name": "temp-concept", "color": "#abc123"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    concept_id = r.json()["id"]

    # Create a transaction linked to that concept
    r = client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "category_id": category["id"],
            "type": "expense",
            "amount": "42.00",
            "currency": "USD",
            "date": "2024-06-01",
            "concept": {"id": concept_id},
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    transaction_id = r.json()["id"]

    # Verify transaction has concept set
    r = client.get(f"/api/v1/transactions/{transaction_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["concept"] is not None

    # Delete the concept
    r = client.delete(f"/api/v1/concept/{concept_id}", headers=auth_headers)
    assert r.status_code == 204

    # Transaction should still exist but concept should be NULL
    r = client.get(f"/api/v1/transactions/{transaction_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["concept"] is None

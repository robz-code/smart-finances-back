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

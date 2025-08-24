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
    }
    r = client.post("/api/v1/accounts", json=create_payload, headers=auth_headers)
    assert r.status_code == 200
    acc = r.json()
    acc_id = acc["id"]
    assert acc["name"] == "Main Wallet"

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

    # Update
    update_payload = {"name": "Updated Wallet"}
    r = client.put(
        f"/api/v1/accounts/{acc_id}", json=update_payload, headers=auth_headers
    )
    assert r.status_code == 200
    updated = r.json()
    assert updated["name"] == "Updated Wallet"

    # Delete
    r = client.delete(f"/api/v1/accounts/{acc_id}", headers=auth_headers)
    assert r.status_code == 204

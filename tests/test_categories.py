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

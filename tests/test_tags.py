def ensure_user(client, auth_headers):
    r = client.post("/api/v1/users", json={"name": "Tag Owner", "email": "tag@example.com"}, headers=auth_headers)
    assert r.status_code == 200


def test_tags_crud_flow(client, auth_headers):
    ensure_user(client, auth_headers)

    # Create
    payload = {"name": "urgent", "color": "#ff0"}
    r = client.post("/api/v1/tags/", json=payload, headers=auth_headers)
    assert r.status_code == 201
    tag = r.json()
    tag_id = tag["id"]
    assert tag["name"] == "urgent"

    # List
    r = client.get("/api/v1/tags/", headers=auth_headers)
    assert r.status_code == 200
    lst = r.json()
    assert lst["total"] >= 1

    # Read one
    r = client.get(f"/api/v1/tags/{tag_id}", headers=auth_headers)
    assert r.status_code == 200
    one = r.json()
    assert one["id"] == tag_id

    # Update
    r = client.put(f"/api/v1/tags/{tag_id}", json={"name": "important"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "important"

    # Delete
    r = client.delete(f"/api/v1/tags/{tag_id}", headers=auth_headers)
    assert r.status_code == 204


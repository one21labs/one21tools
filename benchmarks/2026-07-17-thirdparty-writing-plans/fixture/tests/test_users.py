from taskboard.app import create_app


def test_register_returns_token(tmp_path):
    client = create_app(storage_path=str(tmp_path / "db.json")).test_client()
    r = client.post("/users/", json={"name": "ann"})
    assert r.status_code == 201 and len(r.get_json()["token"]) == 16

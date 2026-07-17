import pytest
from taskboard.app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(storage_path=str(tmp_path / "db.json"))
    return app.test_client()


def _register(client, name="ann"):
    return client.post("/users/", json={"name": name}).get_json()["token"]


def test_create_and_list(client):
    token = _register(client)
    r = client.post("/tasks/", json={"title": "write spec"}, headers={"X-Auth-Token": token})
    assert r.status_code == 201
    r = client.get("/tasks/", headers={"X-Auth-Token": token})
    assert [t["title"] for t in r.get_json()] == ["write spec"]


def test_unauthorized(client):
    assert client.get("/tasks/").status_code == 401


def test_update_own_task_only(client):
    ann, bob = _register(client, "ann"), _register(client, "bob")
    tid = client.post("/tasks/", json={"title": "x"}, headers={"X-Auth-Token": ann}).get_json()["id"]
    assert client.patch(f"/tasks/{tid}", json={"done": True},
                        headers={"X-Auth-Token": bob}).status_code == 404

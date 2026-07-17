"""Task CRUD. All endpoints require a valid X-Auth-Token belonging to a known user."""
from flask import Blueprint, jsonify, request
from taskboard import storage

tasks_bp = Blueprint("tasks", __name__)


def _auth(data):
    token = request.headers.get("X-Auth-Token", "")
    return token if token in data["users"] else None


@tasks_bp.get("/")
def list_tasks():
    data = storage.load()
    if not _auth(data):
        return jsonify(error="unauthorized"), 401
    return jsonify(data["tasks"])


@tasks_bp.post("/")
def create_task():
    data = storage.load()
    owner = _auth(data)
    if not owner:
        return jsonify(error="unauthorized"), 401
    body = request.get_json(force=True)
    task = {"id": storage.next_task_id(data), "title": body["title"],
            "owner": owner, "done": False, "notes": body.get("notes", "")}
    data["tasks"].append(task)
    storage.save(data)
    return jsonify(task), 201


@tasks_bp.patch("/<int:task_id>")
def update_task(task_id):
    data = storage.load()
    owner = _auth(data)
    if not owner:
        return jsonify(error="unauthorized"), 401
    for t in data["tasks"]:
        if t["id"] == task_id and t["owner"] == owner:
            t.update({k: v for k, v in request.get_json(force=True).items()
                      if k in ("title", "done", "notes")})
            storage.save(data)
            return jsonify(t)
    return jsonify(error="not found"), 404

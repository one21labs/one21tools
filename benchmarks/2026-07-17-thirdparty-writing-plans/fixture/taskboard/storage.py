"""Single-file JSON store. Shape: {"users": {token: {"name": ...}}, "tasks": [task, ...]}.
A task: {"id": int, "title": str, "owner": token, "done": bool, "notes": str}."""
import json
import os
from flask import current_app


def _path():
    return current_app.config["STORAGE_PATH"]


def load():
    if not os.path.exists(_path()):
        return {"users": {}, "tasks": []}
    with open(_path()) as f:
        return json.load(f)


def save(data):
    with open(_path(), "w") as f:
        json.dump(data, f, indent=1)


def next_task_id(data):
    return max((t["id"] for t in data["tasks"]), default=0) + 1

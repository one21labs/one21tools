"""User registration: returns the caller's new token. No admin surface."""
import secrets
from flask import Blueprint, jsonify, request
from taskboard import storage

users_bp = Blueprint("users", __name__)


@users_bp.post("/")
def register():
    data = storage.load()
    body = request.get_json(force=True)
    token = secrets.token_hex(8)
    data["users"][token] = {"name": body["name"]}
    storage.save(data)
    return jsonify(token=token), 201

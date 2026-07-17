"""App factory: registers the two route blueprints and wires the storage path."""
import os
from flask import Flask
from taskboard.routes.tasks import tasks_bp
from taskboard.routes.users import users_bp


def create_app(storage_path=None):
    app = Flask(__name__)
    app.config["STORAGE_PATH"] = storage_path or os.environ.get("TASKBOARD_DB", "taskboard-data.json")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(users_bp, url_prefix="/users")
    return app


if __name__ == "__main__":
    create_app().run(port=5000)

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from .models import db
from .services import ensure_runtime_dirs, migrate_database


def create_app(test_config: dict | None = None) -> Flask:
    root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=str(root / "templates"),
        static_folder=str(root / "static"),
    )
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    database_path = Path(app.instance_path) / "notes.db"
    app.config.update(
        SECRET_KEY=os.getenv("NOTES_SECRET_KEY") or os.urandom(32),
        SQLALCHEMY_DATABASE_URI=os.getenv("NOTES_DATABASE_URI", f"sqlite:///{database_path}"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=int(os.getenv("NOTES_MAX_UPLOAD_MB", "64")) * 1024 * 1024,
        UPLOAD_FOLDER=os.getenv("NOTES_UPLOAD_FOLDER", str(Path(app.instance_path) / "uploads")),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        NOTES_VERSION="2.0.0",
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        ensure_runtime_dirs()
        migrate_database()

    return app

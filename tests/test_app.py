import sqlite3

import pytest

from notes_app import create_app
from notes_app.models import Note, Notebook


@pytest.fixture()
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        "MAX_CONTENT_LENGTH": 5 * 1024 * 1024,
    })


@pytest.fixture()
def client(app):
    return app.test_client()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["version"] == "2.0.1"


def test_create_update_search_and_restore(client):
    created = client.post(
        "/api/notes",
        json={
            "title": "SAP VIM",
            "content": "Invoice workflow and procurement notes",
            "tags": ["SAP", "VIM"],
        },
    )
    assert created.status_code == 201
    note_id = created.get_json()["id"]

    updated = client.patch(
        f"/api/notes/{note_id}",
        json={"content": "Invoice workflow and GRN matching", "pinned": True},
    )
    assert updated.status_code == 200
    assert updated.get_json()["pinned"] is True

    search = client.get("/api/search?q=GRN")
    assert search.status_code == 200
    assert any(row["id"] == note_id for row in search.get_json())

    trashed = client.post(f"/api/notes/{note_id}/trash")
    assert trashed.status_code == 200
    trash = client.get("/api/search?view=trash").get_json()
    assert any(row["id"] == note_id for row in trash)

    restored = client.post(f"/api/notes/{note_id}/restore")
    assert restored.status_code == 200
    assert restored.get_json()["deleted"] is False


def test_note_must_be_trashed_before_permanent_delete(client):
    created = client.post("/api/notes", json={"title": "Temporary"}).get_json()
    note_id = created["id"]

    blocked = client.delete(f"/api/notes/{note_id}")
    assert blocked.status_code == 409

    assert client.post(f"/api/notes/{note_id}/trash").status_code == 200
    deleted = client.delete(f"/api/notes/{note_id}")
    assert deleted.status_code == 200
    assert client.get(f"/api/notes/{note_id}").status_code == 404


def test_delete_notebook_moves_notes_to_inbox(client, app):
    notebook = client.post("/api/notebooks", json={"name": "Old project"})
    assert notebook.status_code == 201
    notebook_id = notebook.get_json()["id"]
    note = client.post("/api/notes", json={"title": "Keep me", "notebook_id": notebook_id})
    note_id = note.get_json()["id"]

    deleted = client.delete(f"/api/notebooks/{notebook_id}")
    assert deleted.status_code == 200
    assert deleted.get_json()["moved_notes"] == 1

    moved = client.get(f"/api/notes/{note_id}").get_json()
    assert moved["notebook"] == "Inbox"
    assert moved["notebook_id"] == deleted.get_json()["inbox"]["id"]

    with app.app_context():
        assert Notebook.query.get(notebook_id) is None


def test_inbox_notebook_cannot_be_deleted(client, app):
    with app.app_context():
        inbox_id = Notebook.query.filter_by(name="Inbox").first().id

    response = client.delete(f"/api/notebooks/{inbox_id}")
    assert response.status_code == 409
    assert response.get_json()["error"] == "Inbox cannot be deleted."


def test_markdown_render_is_sanitised(client):
    response = client.post(
        "/api/markdown/render",
        json={
            "content": "# Hello\n\n<script>alert(1)</script>\n\n|A|B|\n|-|-|\n|1|2|",
        },
    )
    assert response.status_code == 200
    html = response.get_json()["html"]
    assert "<h1>Hello</h1>" in html
    assert "<script>" not in html
    assert "<table>" in html


def test_default_inbox_exists(app):
    with app.app_context():
        assert Notebook.query.filter_by(name="Inbox").first() is not None


def test_v1_database_is_migrated_without_losing_notes(tmp_path):
    db_path = tmp_path / "legacy-notes.db"
    connection = sqlite3.connect(db_path)
    connection.execute(
        "CREATE TABLE note ("
        "id INTEGER PRIMARY KEY, "
        "title VARCHAR(100) NOT NULL, "
        "content TEXT NOT NULL, "
        "image VARCHAR(200)"
        ")"
    )
    connection.execute(
        "INSERT INTO note (id, title, content, image) VALUES (?, ?, ?, ?)",
        (1, "Legacy note", "Original content", "old-image.png"),
    )
    connection.commit()
    connection.close()

    migrated = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "UPLOAD_FOLDER": str(tmp_path / "migrated-uploads"),
    })

    with migrated.app_context():
        note = Note.query.get(1)
        assert note is not None
        assert note.title == "Legacy note"
        assert note.content == "Original content"
        assert note.image == "old-image.png"
        assert note.notebook is not None
        assert note.notebook.name == "Inbox"
        assert note.created_at is not None
        assert note.updated_at is not None


def test_ai_server_and_model_can_be_tested_before_saving(client, monkeypatch):
    calls = {}

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    def fake_get(url, timeout):
        calls["models_url"] = url
        calls["models_timeout"] = timeout
        return FakeResponse({"models": [{"name": "qwen2.5-coder:7b"}]})

    def fake_post(url, json, timeout):
        calls["generate_url"] = url
        calls["generate_payload"] = json
        calls["generate_timeout"] = timeout
        return FakeResponse({"response": "Notes AI ready"})

    monkeypatch.setattr("notes_app.services.requests.get", fake_get)
    monkeypatch.setattr("notes_app.services.requests.post", fake_post)

    server = "http://10.0.0.8:11434"
    models = client.get(f"/api/ai/models?url={server}")
    assert models.status_code == 200
    assert models.get_json()["models"] == ["qwen2.5-coder:7b"]
    assert calls["models_url"] == f"{server}/api/tags"

    tested = client.post(
        "/api/ai/test",
        json={
            "ollama_url": server,
            "model": "qwen2.5-coder:7b",
            "timeout_seconds": 45,
        },
    )
    assert tested.status_code == 200
    assert tested.get_json()["model"] == "qwen2.5-coder:7b"
    assert tested.get_json()["ollama_url"] == server
    assert calls["generate_url"] == f"{server}/api/generate"
    assert calls["generate_payload"]["model"] == "qwen2.5-coder:7b"
    assert calls["generate_timeout"] == 45


def test_all_notes_ai_search_handles_conversational_question(app):
    from notes_app.services import context_for_ai, search_notes_for_ai

    with app.app_context():
        inbox = Notebook.query.filter_by(name="Inbox").first()
        sap = Note(
            title="SAP VIM payment terms",
            content="Notes about invoice workflow, GRN matching and supplier payment terms.",
            notebook_id=inbox.id,
        )
        unrelated = Note(
            title="Camper electrics",
            content="Solar panel and MPPT wiring notes.",
            notebook_id=inbox.id,
        )
        db = __import__("notes_app.models", fromlist=["db"]).db
        db.session.add_all([sap, unrelated])
        db.session.commit()

        matches = search_notes_for_ai("What have I written about SAP VIM?", limit=12)
        assert sap.id in [note.id for note in matches]
        assert unrelated.id not in [note.id for note in matches]

        context = context_for_ai(None, "What have I written about SAP VIM?", "all")
        assert "SAP VIM payment terms" in context
        assert "invoice workflow" in context


def test_all_notes_ai_search_can_match_attachment_text(app):
    from notes_app.models import Attachment, db
    from notes_app.services import search_notes_for_ai

    with app.app_context():
        inbox = Notebook.query.filter_by(name="Inbox").first()
        note = Note(title="Supplier meeting", content="General meeting notes", notebook_id=inbox.id)
        db.session.add(note)
        db.session.flush()
        db.session.add(Attachment(
            note_id=note.id,
            original_name="vim.txt",
            stored_name="test-vim.txt",
            mime_type="text/plain",
            size_bytes=20,
            extracted_text="OpenText VIM invoice exception workflow",
        ))
        db.session.commit()

        matches = search_notes_for_ai("find my OpenText VIM information", limit=12)
        assert note.id in [row.id for row in matches]

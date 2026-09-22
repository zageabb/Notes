import pytest

from notes_app import create_app
from notes_app.models import Notebook


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
    assert response.get_json()["version"] == "2.0.0"


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

"""UDA prefix handling without touching persistent note data."""
from notes_app import create_app

def test_uda_proxy_and_lan(tmp_path):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'notes.db'}",
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
    })
    client = app.test_client()
    local = client.get("/")
    assert local.status_code == 200
    assert '<base href="/">' in local.get_data(as_text=True)
    headers = {
        "X-Forwarded-Prefix": "/apps/notes",
        "X-Forwarded-Host": "tanyaanne.ddns.net",
        "X-Forwarded-Proto": "https",
    }
    proxied = client.get("/", headers=headers)
    assert proxied.status_code == 200
    html = proxied.get_data(as_text=True)
    assert '<base href="/apps/notes/">' in html
    assert '/apps/notes/static/js/app.js' in html
    assert client.get("/api/health", headers=headers).status_code == 200

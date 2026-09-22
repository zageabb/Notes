# Notes v2.0.0

Notes is a lightweight local-first personal knowledge workspace. v2 replaces the original single-table Flask notes screen with a three-pane notebook, Markdown editor and local Ollama assistant while preserving the existing SQLite note data.

## Ubuntu server deployment

Verified deployment target:

| Endpoint | Host TCP port | LAN URL |
|---|---:|---|
| Application | 5063 | `http://192.168.1.249:5063/` |

Checkout: `/home/zageabb/flask/Notes`.

Existing user-systemd deployment:

```bash
systemctl --user status migrated-flask@Notes.service
systemctl --user cat migrated-flask@Notes.service
```

The application entry point remains `app.py`. The default runtime port is now 5063 so a direct launch matches the registered server port unless `PORT` or `NOTES_PORT` overrides it.

## v2 features

- responsive three-pane workspace with resizable Notes and AI panes
- notebooks, tags, pinned notes, favourites, archive and Trash
- fast SQLite FTS5 search with a safe LIKE fallback
- Markdown editing and sanitised preview
- Mermaid fenced-block rendering in preview when the browser Mermaid library is available
- autosave with explicit save status and `Cmd/Ctrl+S`
- non-destructive note revision history and restore
- attachments for images, PDF, DOCX, XLSX/XLSM, PPTX, TXT, Markdown, CSV, JSON, XML and LOG
- searchable text extraction from supported document attachments
- local Ollama settings, model discovery and live generation test
- current-note or all-notes AI chat
- review-first AI skills: summarise, improve wording, extract actions, suggest tags/title, create diagrams and find related notes
- reviewable AI title/content/tag proposals before they are written into the editor
- individual Markdown export and complete ZIP backup
- dark/light theme and keyboard search (`Cmd/Ctrl+K`)
- health endpoint at `/api/health`

## Existing database migration

v2 is deliberately additive. At startup it:

1. keeps the existing `note` table and its `id`, `title`, `content` and legacy `image` values;
2. adds the v2 note fields when they are missing;
3. creates Notebook, Tag, Attachment and NoteRevision tables;
4. creates an `Inbox` notebook and assigns existing notes to it;
5. builds the FTS5 index when the local SQLite build supports FTS5.

Back up the `instance/` directory before the first production upgrade even though the migration is non-destructive.

## Local run

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open `http://127.0.0.1:5063/`.

## Ollama

Defaults:

```text
http://192.168.1.249:11434
qwen3:14b
```

Use **Settings** inside Notes to change the Ollama server or model and run a real generation test. Settings are stored under the ignored Flask `instance/` directory.

AI is optional: note capture, Markdown, search, attachments, history and export work without Ollama.

## Configuration

| Variable | Default |
|---|---|
| `NOTES_HOST` | `0.0.0.0` |
| `NOTES_PORT` | `5063` |
| `NOTES_SECRET_KEY` | ephemeral process secret |
| `NOTES_MAX_UPLOAD_MB` | `64` |
| `NOTES_OLLAMA_URL` | `http://192.168.1.249:11434` |
| `NOTES_OLLAMA_MODEL` | `qwen3:14b` |
| `NOTES_OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` |
| `NOTES_DATABASE_URI` | `sqlite:///instance/notes.db` |
| `NOTES_UPLOAD_FOLDER` | `instance/uploads` |

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Documentation

- `DID.md` — architecture and design decisions
- `TODO.md` — v2.1/v2.2 follow-on work
- `RELEASE_NOTES.md` — release changes
- `AGENTS.md` — development guidance for coding agents

## Security boundary

v2 removes the hard-coded Flask secret, validates attachment extensions, bounds uploads, sanitises rendered Markdown and keeps all AI changes review-first. The current deployment remains designed for a trusted LAN. Authentication/roles and stronger CSRF controls are planned before any Internet exposure.

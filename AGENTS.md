# AGENTS.md — Notes

## Purpose

Notes is a lightweight local-first personal knowledge application. Keep capture, navigation and search fast. Do not turn it into a second Context Studio.

## Core rules

1. Preserve existing user notes and attachments during upgrades.
2. AI may answer or propose changes; it must not silently mutate notes/files.
3. Prefer deterministic Python for persistence, extraction, validation and export.
4. Keep Ollama optional. Core note functions must work with AI unavailable.
5. Store runtime data under `instance/`; never commit user notes, uploads or AI settings.
6. Keep `app.py` as a stable deployment entry point unless deployment documentation is updated in the same change.
7. Maintain compatibility with the registered Ubuntu application port 5063.
8. Add tests for schema/migration/API behaviour when changing persistence.

## Current architecture

- Flask 3
- Flask-SQLAlchemy / SQLite
- SQLite FTS5 with fallback
- server-rendered shell + vanilla JavaScript application UI
- local Ollama HTTP API
- PyMuPDF / python-docx / openpyxl / python-pptx extraction

## AI change pattern

For content/title/tag changes:

`skill -> model output -> visible proposal -> user Apply -> standard deterministic update API`

Never give the model direct database or filesystem write tools.

## Follow-on design

See `DID.md`, `TODO.md` and `RELEASE_NOTES.md` before adding major features.

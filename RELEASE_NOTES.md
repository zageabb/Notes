# Release Notes

## v2.0.1 — 22 September 2026

### Changed

- AI Settings now provides explicit Ubuntu, Notes-host and Custom Ollama server choices.
- changing the server reloads the model list from that selected endpoint immediately.
- **Refresh models** uses the URL currently shown in Settings, even before saving.
- **Test AI** uses the currently selected server, model and timeout before saving.
- the AI pane header shows both the active model and Ollama server.

## v2.0.0 — 22 September 2026

Major rebuild of the original Notes Storage application.

### Added

- notebook/tag organisation, pinned notes, favourites, archive and Trash
- responsive resizable three-pane workspace
- Markdown preview, tables, fenced code and Mermaid diagrams
- SQLite FTS5 search with fallback search
- multi-format attachments with document text extraction
- autosave and visible save status
- revision history and non-destructive restore
- local Ollama settings/model discovery/generation testing
- current-note and all-notes assistant modes
- built-in review-first AI Skills
- Markdown note export and complete ZIP backup
- dark/light theme
- health endpoint and automated tests

### Changed

- `app.py` remains the launcher but now uses an application factory.
- default direct-run port is 5063 to match the registered Ubuntu deployment.
- the old database is migrated additively and existing notes are assigned to Inbox.
- Flask secret configuration is no longer hard-coded.
- image-only uploads are replaced by UUID-backed multi-format attachments; the legacy v1 image column remains readable for compatibility.

### Known limitations

- Mermaid is currently loaded by the browser from a CDN.
- semantic embeddings/backlinks are planned for v2.1.
- authentication/CSRF hardening is required before exposing Notes beyond the trusted LAN.
- complete backup export is implemented; package restore is planned for v2.1.

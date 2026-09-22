# Notes Roadmap

## v2.0.0 — implemented

- [x] preserve/migrate v1 notes
- [x] three-pane responsive workspace
- [x] resizable side panes
- [x] notebooks and tags
- [x] pinned/favourite/archive/Trash views
- [x] Markdown preview and Mermaid support
- [x] FTS5 search + fallback
- [x] multi-format attachments and text extraction
- [x] autosave
- [x] revision history and restore
- [x] Ollama setup/model discovery/test
- [x] current/all-notes AI chat
- [x] review-first AI skills and proposals
- [x] Markdown note export
- [x] complete ZIP backup
- [x] dark/light theme
- [x] health endpoint and tests

## v2.1 — knowledge layer

- [ ] embedding-backed semantic search with lexical/semantic hybrid ranking
- [ ] explicit `[[Wiki Links]]` and backlinks
- [ ] similarity-based Related Notes cards
- [ ] AI-proposed note links with Apply/Reject
- [ ] tag management/merge screen
- [ ] notebook rename/reorder/archive
- [ ] richer revision diff view instead of snapshot preview only
- [ ] offline-bundled Mermaid rather than CDN delivery
- [ ] image paste/clipboard capture
- [ ] drag/drop multiple attachments
- [ ] import Markdown folders and ZIP notebook packages
- [ ] restore workflow for complete backup ZIPs

## v2.2 — capture/research integrations

- [ ] General Search research action that saves cited Markdown into Notes
- [ ] URL/web clipping with retrieval date and source metadata
- [ ] Whisper voice-note/transcription integration
- [ ] EML/MSG extraction using the shared document tooling
- [ ] optional localLLM GGUF provider alongside Ollama
- [ ] optional Context Studio send/copy action

## production hardening before Internet exposure

- [ ] optional authentication and roles
- [ ] CSRF protection for browser mutations
- [ ] restrictive trusted-host/CORS deployment profile
- [ ] malware scanning option for uploads
- [ ] managed migration ledger and rollback tooling
- [ ] automated retained SQLite + attachment backups

# Development Status

Last reviewed: 2026-10-02
Current development state: ACTIVE

## Purpose
Common development ledger for the user and AI agents. Existing project-specific planning documents remain valid; this file standardises status and completion evidence.

## Current objective
Notes 2.0/2.x knowledge, search, AI chat, proposals, integrations and production hardening.

## Existing planning and evidence sources
- `TODO.md`
- `DID.md`
- `RELEASE_NOTES.md`
- `tests/`
- `GitHub Actions`

## Status values
- 🔵 PLANNED
- 🔨 IN PROGRESS
- 🚫 BLOCKED
- ⏳ AWAITING ACCEPTANCE
- ✅ COMPLETE
- 💤 DEFERRED

## Evidence standard
An item is COMPLETE only when applicable repository evidence verifies it: implementation, changed files/non-empty diff, tests or recorded no-test reason, passing tests, CI where available, commit/PR evidence, intended-branch merge, and separately recorded external/user acceptance.

For coding work, an empty result, no write/edit action, unchanged branch HEAD, empty diff or missing requested validation means the task is not complete.

## Development ledger

### DEV-000 — Establish evidence-based development ledger
Status: ✅ COMPLETE

Evidence:
- Files: `DEVELOPMENT.md`, `AGENTS.md`
- Git history records these changes.
- Tests: not required for this documentation/process-only change.
- User acceptance: requested 2026-10-02.

### DEV-001 — Delete notes and notebooks safely
Status: ⏳ AWAITING ACCEPTANCE
Priority: High
Owner/Agent: ChatGPT
Branch: main
Depends on: DEV-000
Can run in parallel with: unrelated AI/search work
Integration status: implemented and CI-verified on main

Requirement:
- Allow notes that are no longer required to be permanently removed.
- Allow notebooks that are no longer required to be removed without deleting the notes they contain.

Implementation:
- Permanent note deletion is exposed only for notes already in Trash; the existing API continues to reject direct deletion of active notes.
- Notebook deletion reassigns contained notes to Inbox before removing the notebook.
- Inbox is protected from deletion.
- Notebook and permanent-note deletion both require explicit browser confirmation.

Evidence:
- Files: `notes_app/routes.py`, `templates/index.html`, `static/js/app.js`, `static/css/style.css`, `tests/test_app.py`
- Tests: added API coverage for trash-before-delete, notebook reassignment, and Inbox protection.
- CI: GitHub Actions `Notes tests` run 37485136788 — success.
- Merged to intended branch: implemented directly on `main`.
- User/business acceptance: pending.

Completion criteria:
- [x] Implementation exists.
- [x] Relevant files changed.
- [x] Tests added/updated.
- [x] Relevant tests pass.
- [x] CI passes where applicable.
- [x] Commit evidence exists on `main`.
- [x] Integrated to intended branch.
- [ ] External/user acceptance separated from development completion.

Notes:
- Notebook deletion is intentionally non-destructive: notes are moved to Inbox rather than cascade-deleted.

## Existing backlog/history

Use the project-specific files listed above for historical and detailed backlog entries. New meaningful development should also receive a DEV entry here so status and evidence are visible consistently across repositories.

### OPS-UDA-001 — UDA subpath-compatible Notes
Status: 🔨 IN PROGRESS
Requirement: preserve LAN root use while serving under authenticated UDA `/apps/notes/`.
Implementation: single trusted forwarded prefix in Flask; base-aware assets, API requests, attachment URLs and Markdown exports.
Safety: UDA backend must be ingress-isolated; public proxy settings unchanged.
Evidence: `tests/test_uda_subpath.py`, GitHub Actions `uda-tests.yml`; CI/merge and user testing pending.
- [ ] CI green and merged to main.
- [ ] Browser note editing, autosave, attachments, exports and auth verified through UDA.


### DEV-002 — Mobile screens and installable PWA
Status: ⏳ AWAITING ACCEPTANCE
Priority: High
Owner/Agent: ChatGPT
Branch: main
Integration status: implemented on main; CI and device acceptance still to verify

Requirement:
- Preserve the three-pane desktop workspace.
- Provide phone-sized one-screen Notes/Search/Editor/AI navigation.
- Support home-screen installation through HTTPS while reusing the existing database and APIs.
- Avoid caching private notes or suggesting offline edits are available.

Implementation:
- Dedicated mobile header, four-tab navigation, and small-screen CSS screen modes.
- Selecting or creating notes switches to the editor on narrow screens.
- Web app manifest, SVG icon, and network-only service worker, scoped to the application root (including UDA subpaths).
- Existing desktop layout and note routes remain in place.

Evidence:
- Files: templates/index.html, templates/base.html, static/css/style.css, static/js/app.js, static/manifest.webmanifest, static/icons/notes.svg, static/sw.js, notes_app/routes.py, tests/test_app.py.
- Tests: added test_mobile_pwa_shell_and_assets; CI status to verify.
- Merged to intended branch: commits directly on main.
- User/business acceptance: pending mobile device/HTTPS test.

Remaining:
- [ ] Validate pytest and GitHub Actions CI green.
- [ ] Verify Android install prompt over HTTPS and UDA subpath.
- [ ] Check mobile editing, save, attachment uploads, navigation and AI on real device.
- [x] Added actual 192px and 512px PNG icons and referenced them in manifest (Android install compatibility).
- [ ] Recheck Chrome installation after deployment; proxy/manifest/service-worker accessibility on deployed URL remains unverified.
- [ ] User acceptance.

## New item template

### DEV-XXX — Short title
Status: 🔵 PLANNED
Priority: Medium
Owner/Agent:
Branch:
Depends on:
Can run in parallel with:
Integration status:

Requirement:

Implementation:

Evidence:
- Commit:
- PR:
- Files:
- Tests:
- CI:
- Merged to intended branch:
- User/business acceptance:

Completion criteria:
- [ ] Implementation exists.
- [ ] Relevant files changed.
- [ ] Tests added/updated, or reason recorded.
- [ ] Relevant tests pass.
- [ ] CI passes where applicable.
- [ ] Commit/PR evidence recorded.
- [ ] Merged where required.
- [ ] External/user acceptance separated from development completion.

Notes:

## Parallel development coordination

Use the coordination fields on every active DEV item when parallel work is possible.

- **Owner/Agent** — the person or AI agent currently responsible for the item.
- **Branch** — the working branch or worktree used for the item.
- **Depends on** — DEV items, decisions or external prerequisites that must complete first.
- **Can run in parallel with** — DEV items that are safe to develop concurrently without conflicting ownership or sequencing.
- **Integration status** — for example: not started, isolated, ready for integration, integrated, or integration blocked.

Before starting parallel work, agents should check these fields and avoid claiming the same item, branch or overlapping integration responsibility. If two items touch the same subsystem or files, record the conflict explicitly and sequence or coordinate integration rather than assuming they are independent.

Parallel execution does not weaken the completion standard: each DEV item still requires its own implementation, tests/validation, CI evidence where applicable, and integration/merge evidence before it can be marked COMPLETE.

## Maintenance rule
Update this file during the same development pass that changes implementation. Repository evidence wins when prose disagrees.

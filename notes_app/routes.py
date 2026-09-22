from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import Blueprint, abort, current_app, jsonify, render_template, request, send_file

from .models import Attachment, Note, NoteRevision, Notebook, Tag, db
from .services import (
    SKILLS,
    build_backup_zip,
    context_for_ai,
    delete_attachment_file,
    get_or_create_tags,
    load_ai_settings,
    note_to_dict,
    ollama_generate,
    ollama_models,
    render_markdown,
    run_skill,
    save_ai_settings,
    save_attachment,
    search_notes,
    snapshot_note,
)

bp = Blueprint("notes", __name__)


def _note_or_404(note_id: int) -> Note:
    note = db.session.get(Note, note_id)
    if not note:
        abort(404)
    return note


@bp.get("/")
def index():
    notes = search_notes(view="all", limit=200)
    notebooks = Notebook.query.order_by(Notebook.name.asc()).all()
    tags = Tag.query.order_by(Tag.name.asc()).all()
    selected = notes[0] if notes else None
    return render_template(
        "index.html",
        notes=notes,
        notebooks=notebooks,
        tags=tags,
        selected=selected,
        version=current_app.config["NOTES_VERSION"],
        skills=SKILLS,
    )


@bp.get("/api/health")
def health():
    return jsonify({"status": "ok", "version": current_app.config["NOTES_VERSION"]})


@bp.get("/api/notes/<int:note_id>")
def get_note(note_id: int):
    return jsonify(note_to_dict(_note_or_404(note_id)))


@bp.post("/api/notes")
def create_note():
    data = request.get_json(silent=True) or {}
    notebook = (
        db.session.get(Notebook, data.get("notebook_id"))
        if data.get("notebook_id")
        else Notebook.query.filter_by(name="Inbox").first()
    )
    note = Note(
        title=str(data.get("title") or "Untitled")[:200],
        content=str(data.get("content") or ""),
        notebook_id=notebook.id if notebook else None,
    )
    note.tags = get_or_create_tags(data.get("tags") or [])
    db.session.add(note)
    db.session.commit()
    return jsonify(note_to_dict(note)), 201


@bp.patch("/api/notes/<int:note_id>")
def update_note(note_id: int):
    note = _note_or_404(note_id)
    data = request.get_json(silent=True) or {}
    changed = False
    for field in ("title", "content", "source_url"):
        if field in data:
            value = str(data[field] or "")
            if field == "title":
                value = value.strip()[:200] or "Untitled"
            if getattr(note, field) != value:
                changed = True
    if changed:
        snapshot_note(note)
    if "title" in data:
        note.title = str(data.get("title") or "Untitled").strip()[:200] or "Untitled"
    if "content" in data:
        note.content = str(data.get("content") or "")
    if "source_url" in data:
        note.source_url = str(data.get("source_url") or "").strip() or None
    if "notebook_id" in data:
        notebook = db.session.get(Notebook, data.get("notebook_id"))
        if notebook:
            note.notebook_id = notebook.id
    if "tags" in data:
        note.tags = get_or_create_tags(data.get("tags") or [])
    for field in ("pinned", "favourite"):
        if field in data:
            setattr(note, field, bool(data[field]))
    note.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(note_to_dict(note))


@bp.post("/api/notes/<int:note_id>/archive")
def archive_note(note_id: int):
    note = _note_or_404(note_id)
    snapshot_note(note, force=True)
    note.archived = bool((request.get_json(silent=True) or {}).get("archived", True))
    note.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(note_to_dict(note))


@bp.post("/api/notes/<int:note_id>/trash")
def trash_note(note_id: int):
    note = _note_or_404(note_id)
    snapshot_note(note, force=True)
    note.deleted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"ok": True})


@bp.post("/api/notes/<int:note_id>/restore")
def restore_note(note_id: int):
    note = _note_or_404(note_id)
    note.deleted_at = None
    note.archived = False
    note.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(note_to_dict(note))


@bp.delete("/api/notes/<int:note_id>")
def purge_note(note_id: int):
    note = _note_or_404(note_id)
    if note.deleted_at is None:
        return jsonify({"error": "Move the note to Trash before permanent deletion."}), 409
    for attachment in note.attachments:
        delete_attachment_file(attachment)
    db.session.delete(note)
    db.session.commit()
    return jsonify({"ok": True})


@bp.get("/api/search")
def search():
    query = request.args.get("q", "")
    view = request.args.get("view", "all")
    notebook_id = request.args.get("notebook", type=int)
    notes = search_notes(query=query, notebook_id=notebook_id, view=view, limit=200)
    return jsonify([note_to_dict(note, include_content=False) for note in notes])


@bp.post("/api/notebooks")
def create_notebook():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name") or "").strip()[:120]
    if not name:
        return jsonify({"error": "Notebook name is required."}), 400
    existing = Notebook.query.filter(db.func.lower(Notebook.name) == name.lower()).first()
    if existing:
        return jsonify({"id": existing.id, "name": existing.name})
    notebook = Notebook(name=name)
    db.session.add(notebook)
    db.session.commit()
    return jsonify({"id": notebook.id, "name": notebook.name}), 201


@bp.post("/api/notes/<int:note_id>/attachments")
def upload_attachment(note_id: int):
    note = _note_or_404(note_id)
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "Choose a file."}), 400
    try:
        attachment = save_attachment(file, note)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({
        "id": attachment.id,
        "name": attachment.original_name,
        "has_text": bool(attachment.extracted_text.strip()),
    }), 201


@bp.get("/attachments/<int:attachment_id>")
def attachment_file(attachment_id: int):
    attachment = db.session.get(Attachment, attachment_id)
    if not attachment:
        abort(404)
    path = Path(current_app.config["UPLOAD_FOLDER"]) / attachment.stored_name
    if not path.exists():
        abort(404)
    return send_file(
        path,
        download_name=attachment.original_name,
        mimetype=attachment.mime_type,
        as_attachment=False,
    )


@bp.delete("/api/attachments/<int:attachment_id>")
def delete_attachment(attachment_id: int):
    attachment = db.session.get(Attachment, attachment_id)
    if not attachment:
        abort(404)
    delete_attachment_file(attachment)
    db.session.delete(attachment)
    db.session.commit()
    return jsonify({"ok": True})


@bp.post("/api/markdown/render")
def markdown_preview():
    data = request.get_json(silent=True) or {}
    return jsonify({"html": render_markdown(str(data.get("content") or ""))})


@bp.get("/api/notes/<int:note_id>/versions")
def versions(note_id: int):
    _note_or_404(note_id)
    rows = (
        NoteRevision.query.filter_by(note_id=note_id)
        .order_by(NoteRevision.created_at.desc())
        .limit(100)
        .all()
    )
    return jsonify([
        {
            "id": row.id,
            "title": row.title,
            "content": row.content,
            "tags": row.tags_csv,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ])


@bp.post("/api/notes/<int:note_id>/versions/<int:revision_id>/restore")
def restore_version(note_id: int, revision_id: int):
    note = _note_or_404(note_id)
    revision = db.session.get(NoteRevision, revision_id)
    if not revision or revision.note_id != note.id:
        abort(404)
    snapshot_note(note, force=True)
    note.title = revision.title
    note.content = revision.content
    note.notebook_id = revision.notebook_id or note.notebook_id
    note.tags = get_or_create_tags([
        x.strip()
        for x in revision.tags_csv.split(",")
        if x.strip()
    ])
    note.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(note_to_dict(note))


@bp.get("/api/ai/settings")
def ai_settings_get():
    return jsonify(load_ai_settings())


@bp.post("/api/ai/settings")
def ai_settings_save():
    try:
        return jsonify(save_ai_settings(request.get_json(silent=True) or {}))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.get("/api/ai/models")
def ai_models():
    try:
        return jsonify({
            "models": ollama_models(request.args.get("url")),
            "ollama_url": request.args.get("url") or load_ai_settings()["ollama_url"],
        })
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Ollama model discovery failed: {exc}"}), 502


@bp.post("/api/ai/test")
def ai_test():
    data = request.get_json(silent=True) or {}
    override = {
        key: data[key]
        for key in ("ollama_url", "model", "timeout_seconds")
        if key in data
    }
    try:
        response = ollama_generate(
            "Reply with exactly: Notes AI ready",
            settings_override=override or None,
        )
        active = load_ai_settings()
        return jsonify({
            "ok": True,
            "response": response,
            "ollama_url": override.get("ollama_url", active["ollama_url"]),
            "model": override.get("model", active["model"]),
        })
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 502


@bp.get("/api/ai/skills")
def ai_skills():
    return jsonify([{"id": key, **value} for key, value in SKILLS.items()])


@bp.post("/api/ai/chat")
def ai_chat():
    data = request.get_json(silent=True) or {}
    question = str(data.get("message") or "").strip()
    if not question:
        return jsonify({"error": "Message is required."}), 400
    note = db.session.get(Note, data.get("note_id")) if data.get("note_id") else None
    scope = "all" if data.get("scope") == "all" else "current"
    context = context_for_ai(note, question, scope)
    prompt = f"QUESTION:\n{question}\n\nNOTES CONTEXT:\n{context}"
    try:
        answer = ollama_generate(
            prompt,
            system=(
                "You are Notes, a local personal knowledge assistant. "
                "Answer from the supplied context. State clearly when the notes "
                "do not contain the answer. Use concise Markdown."
            ),
        )
        return jsonify({"answer": answer})
    except Exception as exc:
        return jsonify({"error": f"AI request failed: {exc}"}), 502


@bp.post("/api/ai/skill")
def ai_skill():
    data = request.get_json(silent=True) or {}
    note = db.session.get(Note, data.get("note_id")) if data.get("note_id") else None
    if not note:
        return jsonify({"error": "Select a note first."}), 400
    try:
        return jsonify(run_skill(
            note,
            str(data.get("skill") or ""),
            str(data.get("instruction") or ""),
        ))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"AI skill failed: {exc}"}), 502


@bp.get("/export/note/<int:note_id>.md")
def export_note(note_id: int):
    note = _note_or_404(note_id)
    body = f"# {note.title}\n\n{note.content or ''}\n"
    return current_app.response_class(
        body,
        mimetype="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="note-{note.id}.md"'},
    )


@bp.get("/export/backup.zip")
def export_backup():
    return send_file(
        build_backup_zip(),
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"notes-backup-{datetime.utcnow().date().isoformat()}.zip",
    )

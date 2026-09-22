from __future__ import annotations

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

note_tags = db.Table(
    "note_tags",
    db.Column("note_id", db.Integer, db.ForeignKey("note.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True),
)


class Notebook(db.Model):
    __tablename__ = "notebook"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Tag(db.Model):
    __tablename__ = "tag"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True, index=True)


class Note(db.Model):
    __tablename__ = "note"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, default="Untitled")
    content = db.Column(db.Text, nullable=False, default="")
    image = db.Column(db.String(200))  # legacy v1 image field retained for compatibility
    notebook_id = db.Column(db.Integer, db.ForeignKey("notebook.id"), nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    pinned = db.Column(db.Boolean, nullable=False, default=False)
    favourite = db.Column(db.Boolean, nullable=False, default=False)
    archived = db.Column(db.Boolean, nullable=False, default=False)
    source_url = db.Column(db.String(1000), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    metadata_json = db.Column(db.Text, nullable=False, default="{}")

    notebook = db.relationship("Notebook", backref=db.backref("notes", lazy=True))
    tags = db.relationship("Tag", secondary=note_tags, lazy="selectin", backref=db.backref("notes", lazy="dynamic"))
    attachments = db.relationship("Attachment", backref="note", lazy="selectin", cascade="all, delete-orphan")


class Attachment(db.Model):
    __tablename__ = "attachment"
    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey("note.id", ondelete="CASCADE"), nullable=False, index=True)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False, unique=True)
    mime_type = db.Column(db.String(160), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=False, default=0)
    extracted_text = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class NoteRevision(db.Model):
    __tablename__ = "note_revision"
    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey("note.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    notebook_id = db.Column(db.Integer, nullable=True)
    tags_csv = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    note = db.relationship("Note", backref=db.backref("revisions", lazy="dynamic", cascade="all, delete-orphan"))

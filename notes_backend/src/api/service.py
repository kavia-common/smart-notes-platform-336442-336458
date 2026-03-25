from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import desc, or_, select

from src.api.db import Database, Note, Tag
from src.api.errors import ConflictError, NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ListNotesRequest:
    """Contract for listing notes."""
    q: str | None
    tag: str | None
    limit: int
    offset: int
    sort: Literal["updated_desc", "created_desc"]


@dataclass(frozen=True)
class SearchNotesRequest:
    """Contract for searching notes."""
    q: str
    mode: Literal["all", "title", "content", "tags"]
    limit: int
    offset: int


def _note_to_out_dict(note: Note) -> dict:
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "tags": note.tags or [],
        "created_at": note.created_at,
        "updated_at": note.updated_at,
    }


def _ensure_tags_exist(db: Database, tags: list[str]) -> None:
    """Upsert tags table rows for given tag names."""
    if not tags:
        return
    with db.session() as s:
        existing = {t.name for t in s.execute(select(Tag).where(Tag.name.in_(tags))).scalars().all()}
        missing = [t for t in tags if t not in existing]
        for name in missing:
            s.add(Tag(name=name))


# PUBLIC_INTERFACE
def create_note_flow(db: Database, *, title: str, content: str, tags: list[str]) -> dict:
    """Create a note and return serialized output dict."""
    logger.info("create_note_flow.start", extra={"title_len": len(title), "tag_count": len(tags)})
    _ensure_tags_exist(db, tags)
    with db.session() as s:
        note = Note(title=title, content=content, tags=tags)
        s.add(note)
        s.flush()
        s.refresh(note)
        out = _note_to_out_dict(note)
    logger.info("create_note_flow.ok", extra={"note_id": out["id"]})
    return out


# PUBLIC_INTERFACE
def get_note_flow(db: Database, *, note_id: int) -> dict:
    """Fetch a single note by id."""
    with db.session() as s:
        note = s.get(Note, note_id)
        if note is None:
            raise NotFoundError(message="Note not found", details={"note_id": note_id})
        return _note_to_out_dict(note)


# PUBLIC_INTERFACE
def update_note_flow(db: Database, *, note_id: int, patch: dict) -> dict:
    """Update a note by id with a patch dict (validated at API boundary)."""
    logger.info("update_note_flow.start", extra={"note_id": note_id})
    tags = patch.get("tags")
    if tags is not None:
        _ensure_tags_exist(db, tags)

    with db.session() as s:
        note = s.get(Note, note_id)
        if note is None:
            raise NotFoundError(message="Note not found", details={"note_id": note_id})

        if "title" in patch and patch["title"] is not None:
            note.title = patch["title"]
        if "content" in patch and patch["content"] is not None:
            note.content = patch["content"]
        if "tags" in patch and patch["tags"] is not None:
            note.tags = patch["tags"]

        s.add(note)
        s.flush()
        s.refresh(note)
        out = _note_to_out_dict(note)

    logger.info("update_note_flow.ok", extra={"note_id": note_id})
    return out


# PUBLIC_INTERFACE
def delete_note_flow(db: Database, *, note_id: int) -> None:
    """Delete a note by id."""
    logger.info("delete_note_flow.start", extra={"note_id": note_id})
    with db.session() as s:
        note = s.get(Note, note_id)
        if note is None:
            raise NotFoundError(message="Note not found", details={"note_id": note_id})
        s.delete(note)
    logger.info("delete_note_flow.ok", extra={"note_id": note_id})


# PUBLIC_INTERFACE
def list_notes_flow(db: Database, req: ListNotesRequest) -> tuple[list[dict], int]:
    """List notes with optional filtering."""
    with db.session() as s:
        stmt = select(Note)
        if req.tag:
            # Tags stored as JSON array; easiest portable filter is ILIKE on serialized content.
            # Note: acceptable for v1; can be replaced with normalized join on NoteTag later.
            stmt = stmt.where(Note.tags.cast(str).ilike(f'%"{req.tag}"%'))

        if req.q:
            q = f"%{req.q}%"
            stmt = stmt.where(or_(Note.title.ilike(q), Note.content.ilike(q)))

        if req.sort == "created_desc":
            stmt = stmt.order_by(desc(Note.created_at))
        else:
            stmt = stmt.order_by(desc(Note.updated_at))

        # total
        total = len(s.execute(stmt).scalars().all())
        # page
        page_stmt = stmt.limit(req.limit).offset(req.offset)
        notes = s.execute(page_stmt).scalars().all()
        return ([_note_to_out_dict(n) for n in notes], total)


# PUBLIC_INTERFACE
def search_notes_flow(db: Database, req: SearchNotesRequest) -> tuple[list[dict], int]:
    """Search notes by query and mode."""
    if not req.q.strip():
        raise ConflictError(message="Search query cannot be empty")

    with db.session() as s:
        stmt = select(Note)
        q = f"%{req.q}%"
        if req.mode == "title":
            stmt = stmt.where(Note.title.ilike(q))
        elif req.mode == "content":
            stmt = stmt.where(Note.content.ilike(q))
        elif req.mode == "tags":
            stmt = stmt.where(Note.tags.cast(str).ilike(f"%{req.q}%"))
        else:
            stmt = stmt.where(or_(Note.title.ilike(q), Note.content.ilike(q), Note.tags.cast(str).ilike(f"%{req.q}%")))

        stmt = stmt.order_by(desc(Note.updated_at))

        total = len(s.execute(stmt).scalars().all())
        notes = s.execute(stmt.limit(req.limit).offset(req.offset)).scalars().all()
        return ([_note_to_out_dict(n) for n in notes], total)


# PUBLIC_INTERFACE
def list_tags_flow(db: Database) -> list[dict]:
    """List all tags with approximate counts based on JSON tags array."""
    with db.session() as s:
        tags = s.execute(select(Tag).order_by(Tag.name.asc())).scalars().all()
        # approximate count: scan notes for each tag (fine for small app; can be optimized later)
        notes = s.execute(select(Note.id, Note.tags)).all()
        counts: dict[str, int] = {t.name: 0 for t in tags}
        for _, tag_list in notes:
            for t in (tag_list or []):
                if t in counts:
                    counts[t] += 1
        return [{"name": t.name, "count": counts.get(t.name, 0)} for t in tags]

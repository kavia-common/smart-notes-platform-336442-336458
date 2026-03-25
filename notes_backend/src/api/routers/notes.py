from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.api.db import Database
from src.api.errors import ErrorResponse
from src.api.models import NoteCreate, NoteOut, NoteUpdate
from src.api.service import (
    ListNotesRequest,
    create_note_flow,
    delete_note_flow,
    get_note_flow,
    list_notes_flow,
    update_note_flow,
)
from src.api.wiring import get_db

router = APIRouter(prefix="/notes", tags=["Notes"])


@router.get(
    "",
    summary="List notes",
    description="List notes with optional full-text-ish query and tag filter.",
    response_model=dict,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def list_notes(
    q: str | None = Query(default=None, description="Optional query to match title/content."),
    tag: str | None = Query(default=None, description="Optional tag filter."),
    limit: int = Query(default=50, ge=1, le=200, description="Max items to return."),
    offset: int = Query(default=0, ge=0, description="Pagination offset."),
    sort: str = Query(default="updated_desc", description="Sort order: updated_desc or created_desc."),
    db: Database = Depends(get_db),
):
    items, total = list_notes_flow(
        db,
        ListNotesRequest(q=q, tag=tag, limit=limit, offset=offset, sort=sort),  # type: ignore[arg-type]
    )
    return {"items": items, "total": total}


@router.post(
    "",
    summary="Create note",
    description="Create a new note.",
    response_model=NoteOut,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def create_note(payload: NoteCreate, db: Database = Depends(get_db)) -> NoteOut:
    out = create_note_flow(db, title=payload.title, content=payload.content, tags=payload.tags)
    return NoteOut(**out)


@router.get(
    "/{note_id}",
    summary="Get note",
    description="Retrieve a note by ID.",
    response_model=NoteOut,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def get_note(note_id: int, db: Database = Depends(get_db)) -> NoteOut:
    out = get_note_flow(db, note_id=note_id)
    return NoteOut(**out)


@router.put(
    "/{note_id}",
    summary="Update note",
    description="Update an existing note by ID.",
    response_model=NoteOut,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def update_note(note_id: int, payload: NoteUpdate, db: Database = Depends(get_db)) -> NoteOut:
    patch = payload.model_dump(exclude_unset=True)
    out = update_note_flow(db, note_id=note_id, patch=patch)
    return NoteOut(**out)


@router.delete(
    "/{note_id}",
    summary="Delete note",
    description="Delete a note by ID.",
    response_model=dict,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def delete_note(note_id: int, db: Database = Depends(get_db)):
    delete_note_flow(db, note_id=note_id)
    return {"deleted": True, "id": note_id}

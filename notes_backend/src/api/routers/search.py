from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.api.db import Database
from src.api.errors import ErrorResponse
from src.api.models import NoteOut, SearchResponse
from src.api.service import SearchNotesRequest, search_notes_flow
from src.api.wiring import get_db

router = APIRouter(prefix="/search", tags=["Search"])


@router.get(
    "",
    summary="Search notes",
    description="Search notes by query across title/content/tags.",
    response_model=SearchResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def search_notes(
    q: str = Query(..., min_length=1, description="Search query."),
    mode: str = Query(default="all", description="Search mode: all|title|content|tags."),
    limit: int = Query(default=50, ge=1, le=200, description="Max items to return."),
    offset: int = Query(default=0, ge=0, description="Pagination offset."),
    db: Database = Depends(get_db),
) -> SearchResponse:
    items, total = search_notes_flow(
        db,
        SearchNotesRequest(q=q, mode=mode, limit=limit, offset=offset),  # type: ignore[arg-type]
    )
    return SearchResponse(items=[NoteOut(**n) for n in items], total=total)

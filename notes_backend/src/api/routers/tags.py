from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.db import Database
from src.api.errors import ErrorResponse
from src.api.models import TagOut
from src.api.service import list_tags_flow
from src.api.wiring import get_db

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get(
    "",
    summary="List tags",
    description="List all tags with counts.",
    response_model=list[TagOut],
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def list_tags(db: Database = Depends(get_db)) -> list[TagOut]:
    items = list_tags_flow(db)
    return [TagOut(**t) for t in items]

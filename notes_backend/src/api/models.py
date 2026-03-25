from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _normalize_tags(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    seen = set()
    for t in tags:
        t2 = t.strip()
        if not t2:
            continue
        key = t2.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(t2)
    return normalized


class NoteBase(BaseModel):
    title: str = Field("", max_length=200, description="Note title.")
    content: str = Field("", description="Note markdown/plaintext content.")
    tags: list[str] = Field(default_factory=list, description="List of tags for the note.")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        return _normalize_tags(v)


class NoteCreate(NoteBase):
    """Payload to create a note."""


class NoteUpdate(BaseModel):
    """Payload to update a note (partial)."""

    title: str | None = Field(default=None, max_length=200, description="Updated note title.")
    content: str | None = Field(default=None, description="Updated content.")
    tags: list[str] | None = Field(default=None, description="Updated tags list.")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        return None if v is None else _normalize_tags(v)


class NoteOut(NoteBase):
    id: int = Field(..., description="Note ID.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")


class TagOut(BaseModel):
    name: str = Field(..., description="Tag name.")
    count: int = Field(..., ge=0, description="Number of notes with this tag.")


class SearchMode(BaseModel):
    mode: Literal["all", "title", "content", "tags"] = Field(
        "all", description="Which fields to search."
    )


class SearchResponse(BaseModel):
    items: list[NoteOut] = Field(..., description="Matching notes.")
    total: int = Field(..., ge=0, description="Total number of matches (before pagination).")

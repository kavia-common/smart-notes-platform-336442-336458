from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from src.api.errors import DatabaseError

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy Declarative base."""


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Store tags redundantly as JSON array to simplify frontend usage and search.
    # Invariant: tags is a list[str] with unique, non-empty elements (enforced at service layer).
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Optional future proof: link table exists for normalization/advanced queries later
    note_tags: Mapped[list["NoteTag"]] = relationship(
        back_populates="note", cascade="all, delete-orphan"
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NoteTag(Base):
    __tablename__ = "note_tags"
    __table_args__ = (UniqueConstraint("note_id", "tag_id", name="uq_note_tag"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    note: Mapped[Note] = relationship(back_populates="note_tags")
    tag: Mapped[Tag] = relationship()


class Database:
    """DB adapter encapsulating SQLAlchemy engine/session lifecycle."""

    def __init__(self, postgres_url: str) -> None:
        self._engine = create_engine(postgres_url, pool_pre_ping=True)
        self._SessionLocal = sessionmaker(bind=self._engine, autoflush=False, autocommit=False)

    def create_schema(self) -> None:
        """Create tables if they don't exist."""
        try:
            Base.metadata.create_all(self._engine)
        except Exception as e:  # noqa: BLE001 - boundary: add context and rethrow
            raise DatabaseError(message="Failed to create database schema") from e

    @contextmanager
    def session(self):
        """Provide a transactional session scope."""
        db = self._SessionLocal()
        try:
            yield db
            db.commit()
        except Exception as e:  # noqa: BLE001
            db.rollback()
            logger.exception("db_session_failed")
            raise DatabaseError(message="Database operation failed") from e
        finally:
            db.close()


# PUBLIC_INTERFACE
def build_database(postgres_url: str | None) -> Database:
    """Construct Database adapter from a URL.

    Args:
        postgres_url: SQLAlchemy-compatible postgres URL from env var POSTGRES_URL.

    Returns:
        Database: adapter instance.

    Raises:
        DatabaseError: if postgres_url is missing/invalid.
    """
    if not postgres_url:
        raise DatabaseError(
            message="POSTGRES_URL is not configured",
            details={"env_var": "POSTGRES_URL"},
        )
    return Database(postgres_url)

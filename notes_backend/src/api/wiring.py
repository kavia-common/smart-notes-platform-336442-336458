from __future__ import annotations

from functools import lru_cache



from src.api.config import get_settings
from src.api.db import Database, build_database


@lru_cache(maxsize=1)
def _db_singleton() -> Database:
    settings = get_settings()
    db = build_database(settings.postgres_url)
    db.create_schema()
    return db


# PUBLIC_INTERFACE
def get_db() -> Database:
    """FastAPI dependency that returns a singleton Database adapter.

    Returns:
        Database: ready-to-use DB adapter with schema ensured.
    """
    return _db_singleton()

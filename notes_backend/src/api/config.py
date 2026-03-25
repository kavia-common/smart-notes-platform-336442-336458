import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables.

    Contract:
    - Inputs: environment variables
        - POSTGRES_URL: SQLAlchemy-compatible PostgreSQL URL (preferred)
        - FRONTEND_ORIGIN: the Next.js origin to allow via CORS (optional; defaults to '*')
    - Outputs: strongly typed settings object
    - Errors: none (validation occurs in DB layer where needed)
    """

    postgres_url: str | None
    frontend_origin: str | None


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load settings from environment variables.

    Returns:
        Settings: normalized settings for the application.
    """
    return Settings(
        postgres_url=os.getenv("POSTGRES_URL"),
        frontend_origin=os.getenv("FRONTEND_ORIGIN"),
    )

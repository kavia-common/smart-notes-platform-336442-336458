from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Serialized error shape used for all API failures."""
    code: str = Field(..., description="Stable machine-readable error code.")
    message: str = Field(..., description="Human-readable error message.")
    details: dict[str, Any] | None = Field(
        default=None, description="Optional structured error details."
    )


class ApiError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class NotFoundError(ApiError):
    """Raised when a resource is not found."""

    def __init__(self, *, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(code="not_found", message=message, status_code=404, details=details)


class ConflictError(ApiError):
    """Raised when an operation violates a uniqueness or state constraint."""

    def __init__(self, *, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(code="conflict", message=message, status_code=409, details=details)


class DatabaseError(ApiError):
    """Raised for unexpected DB failures."""

    def __init__(self, *, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="database_error",
            message=message,
            status_code=500,
            details=details,
        )


# PUBLIC_INTERFACE
def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    """FastAPI exception handler for ApiError.

    Args:
        _: request (unused)
        exc: raised ApiError

    Returns:
        JSONResponse: consistent error shape.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(code=exc.code, message=exc.message, details=exc.details).model_dump(),
    )

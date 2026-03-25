import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import get_settings
from src.api.errors import ApiError, api_error_handler
from src.api.routers import notes as notes_router
from src.api.routers import search as search_router
from src.api.routers import tags as tags_router

logging.basicConfig(level=logging.INFO)

openapi_tags = [
    {"name": "System", "description": "Health and meta endpoints."},
    {"name": "Notes", "description": "CRUD operations for notes."},
    {"name": "Tags", "description": "Tag listing and metadata."},
    {"name": "Search", "description": "Search endpoints."},
]

app = FastAPI(
    title="Smart Notes Platform API",
    description=(
        "Backend API for the Smart Notes Platform.\n\n"
        "Provides Notes CRUD, Tags listing, and Search.\n"
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# Consistent error handling
app.add_exception_handler(ApiError, api_error_handler)

# CORS: allow configured frontend origin (default permissive only if not provided)
settings = get_settings()
allow_origins = ["*"] if not settings.frontend_origin else [settings.frontend_origin]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    tags=["System"],
    summary="Health check",
    description="Simple health check endpoint.",
)
def health_check():
    """Health check endpoint.

    Returns:
        dict: {"message": "Healthy"}
    """
    return {"message": "Healthy"}


app.include_router(notes_router.router)
app.include_router(tags_router.router)
app.include_router(search_router.router)

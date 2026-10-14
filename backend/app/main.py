"""
VanMitra Module 4 (VanRozgar) backend.

Run locally:  uvicorn app.main:app --reload --port 8010
API docs:     http://localhost:8010/docs

Standalone for now. At merge, only `app/livelihood/` moves into the host and its router is
included next to the others in the host's `app/api/v1/__init__.py` (docs/INTEGRATION.md).
"""

from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import get_settings
from .errors import install_error_handlers
from .livelihood.router import router as livelihood_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="VanMitra Module 4 API",
        description=(
            "Personal livelihood report for one landowner. It suggests; the landowner decides, "
            "and for community forest the Gram Sabha decides."
        ),
        version=__version__,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_error_handlers(app)

    v1 = APIRouter(prefix="/api/v1")

    @v1.get("/health", tags=["health"])
    def health() -> dict[str, Any]:
        # `database` becomes a real ping in slice 2 (MongoDB).
        return {"status": "ok", "database": "not_configured", "version": __version__}

    v1.include_router(livelihood_router)
    app.include_router(v1)

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, Any]:
        return {"service": "vanmitra-livelihood", "version": __version__, "docs": "/docs"}

    return app


app = create_app()

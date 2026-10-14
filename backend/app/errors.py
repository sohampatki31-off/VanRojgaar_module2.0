"""
Uniform error responses, same shape as the host app (vanmitra_backend/app/errors.py):

    {"error": "...", "message_key": "...", "details": {...}}

The app shows a plain-language message from `message_key`, never a raw code.
Module 4 has no statutory blocks, so there is no `rule` field here.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        error: str,
        message_key: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(error)
        self.status_code = status_code
        self.error = error
        self.message_key = message_key
        self.details = details or {}


def _body(error: str, message_key: str, details: dict[str, Any]) -> dict[str, Any]:
    return {"error": error, "message_key": message_key, "details": jsonable_encoder(details)}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code, content=_body(exc.error, exc.message_key, exc.details)
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        problems = [
            {"where": ".".join(str(p) for p in e["loc"]), "type": e["type"]} for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_body("VALIDATION_ERROR", "error.validation", {"problems": problems}),
        )

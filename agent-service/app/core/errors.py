from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.tracing import get_request_id
from app.schemas.errors import APIErrorResponse


class AppError(Exception):
    # English comments only
    def __init__(self, error_code: str, message: str, status_code: int = 400, details: Any = None):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        payload = APIErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            request_id=get_request_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        payload = APIErrorResponse(
            error_code="INTERNAL_ERROR",
            message="Unhandled server error.",
            details={"type": exc.__class__.__name__},
            request_id=get_request_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return JSONResponse(status_code=500, content=payload.model_dump())
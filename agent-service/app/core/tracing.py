import contextvars
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

request_id_ctx = contextvars.ContextVar("request_id", default=None)


def get_request_id() -> str:
    # English comments only
    rid = request_id_ctx.get()
    return rid or "unknown"


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # English comments only
        incoming = request.headers.get("X-Request-ID")
        rid = incoming or str(uuid.uuid4())
        request_id_ctx.set(rid)

        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response
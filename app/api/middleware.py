from time import perf_counter
from uuid import uuid4

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__, component="api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log HTTP requests with isolated context and without query strings."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=str(uuid4()),
            method=request.method,
            path=request.url.path,
            component="api",
        )
        started = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            logger.info(
                "request_completed", status_code=status_code, duration_ms=round((perf_counter() - started) * 1000, 2)
            )
            structlog.contextvars.clear_contextvars()

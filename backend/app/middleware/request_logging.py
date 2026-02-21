"""
Request logging middleware for tracing and debugging.

Logs each request: method, path, query string, status code, and duration.
Use LOG_LEVEL=DEBUG for more verbose application logs; request lines are logged at INFO.
"""

import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log HTTP method, path, query, status code, and duration for each request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        method = request.method
        path = request.url.path
        query = request.url.query
        path_with_query = f"{path}?{query}" if query else path
        try:
            response = await call_next(request)
            status = response.status_code
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "%s %s %s %.1fms",
                method,
                path_with_query,
                status,
                duration_ms,
            )
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "%s %s ERROR after %.1fms: %s",
                method,
                path_with_query,
                duration_ms,
                exc,
            )
            raise

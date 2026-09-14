import logging
import time
from collections import defaultdict, deque
from threading import Lock
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import Settings
from app.core.context import request_id_context


logger = logging.getLogger("finsight.http")


def error_payload(code: str, message: str, retryable: bool, request_id: str) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "request_id": request_id,
        }
    }


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid4().hex[:12]}"
        request.state.request_id = request_id
        token = request_id_context.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                "request.completed",
                extra={
                    "fields": {
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": elapsed_ms,
                    }
                },
            )
            request_id_context.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestGuardMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "POST" and request.url.path.endswith("/query"):
            request_id = getattr(request.state, "request_id", "unknown")
            content_length = request.headers.get("content-length")
            try:
                declared_size = int(content_length) if content_length else 0
            except ValueError:
                declared_size = self.settings.max_request_bytes + 1
            body = await request.body()
            if (
                declared_size > self.settings.max_request_bytes
                or len(body) > self.settings.max_request_bytes
            ):
                return JSONResponse(
                    status_code=413,
                    content=error_payload(
                        "REQUEST_TOO_LARGE",
                        "The request body is too large.",
                        False,
                        request_id,
                    ),
                )
            client_key = request.client.host if request.client else "unknown"
            now = time.monotonic()
            with self._lock:
                history = self._requests[client_key]
                cutoff = now - self.settings.rate_limit_window_seconds
                while history and history[0] <= cutoff:
                    history.popleft()
                if len(history) >= self.settings.rate_limit_requests:
                    retry_after = max(1, int(history[0] + self.settings.rate_limit_window_seconds - now))
                    return JSONResponse(
                        status_code=429,
                        headers={"Retry-After": str(retry_after)},
                        content=error_payload(
                            "RATE_LIMITED",
                            "Too many requests. Please wait before trying again.",
                            True,
                            request_id,
                        ),
                    )
                history.append(now)
        return await call_next(request)

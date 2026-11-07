import hmac
from collections import defaultdict, deque
from http.cookies import SimpleCookie
from threading import Lock
from time import monotonic

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from evalworks.auth import CSRF_COOKIE, SESSION_COOKIE
from evalworks.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_windows: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()
_SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"cache-control", b"no-store"),
    (
        b"content-security-policy",
        b"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; "
        b"img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
    ),
]


def require_api_key(provided: str | None = Depends(api_key_header)) -> str:
    if not provided or not hmac.compare_digest(provided, settings.api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return provided


class RequestLimitsMiddleware:
    """Pure ASGI body-size and single-process rate limits, compatible with streamed responses."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def secure_send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                names = {name.lower() for name, _ in headers}
                headers.extend(
                    (name, value) for name, value in _SECURITY_HEADERS if name not in names
                )
                message["headers"] = headers
            await send(message)

        messages = []
        body_size = 0
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] == "http.disconnect":
                break
            if message["type"] == "http.request":
                body_size += len(message.get("body", b""))
                if body_size > settings.max_request_bytes:
                    response = JSONResponse(
                        status_code=413,
                        content={"detail": "Request body exceeds configured limit"},
                    )
                    await response(scope, receive, secure_send)
                    return
                if not message.get("more_body", False):
                    break

        request_headers = {name.lower(): value for name, value in scope.get("headers", [])}
        cookie = SimpleCookie()
        cookie.load(request_headers.get(b"cookie", b"").decode("latin-1"))
        session = cookie.get(SESSION_COOKIE)
        method = scope.get("method", "GET").upper()
        path = scope.get("path", "")
        if (
            session
            and method in {"POST", "PUT", "PATCH", "DELETE"}
            and path != "/api/v1/auth/login"
        ):
            csrf_cookie = cookie.get(CSRF_COOKIE)
            csrf_header = request_headers.get(b"x-csrf-token", b"").decode("latin-1")
            if (
                not csrf_cookie
                or not csrf_header
                or not hmac.compare_digest(csrf_cookie.value, csrf_header)
            ):
                response = JSONResponse(status_code=403, content={"detail": "CSRF check failed"})
                await response(scope, receive, secure_send)
                return

        client = scope.get("client")
        host = client[0] if client else "unknown"
        bucket_key = f"{host}:{'login' if path == '/api/v1/auth/login' else 'general'}"
        now = monotonic()
        with _lock:
            bucket = _windows[bucket_key]
            while bucket and now - bucket[0] > 60:
                bucket.popleft()
            request_limit = 10 if path == "/api/v1/auth/login" else 120
            if len(bucket) >= request_limit:
                response = JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
                await response(scope, receive, secure_send)
                return
            bucket.append(now)
            if len(_windows) > 10_000:
                for stale_host in [key for key, events in _windows.items() if not events]:
                    _windows.pop(stale_host, None)

        message_index = 0

        async def replay_receive():
            nonlocal message_index
            if message_index < len(messages):
                message = messages[message_index]
                message_index += 1
                return message
            return await receive()

        await self.app(scope, replay_receive, secure_send)

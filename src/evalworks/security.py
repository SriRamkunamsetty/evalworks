import hmac
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

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
            if message["type"] == "http.disconnect":
                messages.append(message)
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
                messages.append(message)
                if not message.get("more_body", False):
                    break
            else:
                messages.append(message)
                break

        client = scope.get("client")
        host = client[0] if client else "unknown"
        now = monotonic()
        with _lock:
            bucket = _windows[host]
            while bucket and now - bucket[0] > 60:
                bucket.popleft()
            if len(bucket) >= 120:
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

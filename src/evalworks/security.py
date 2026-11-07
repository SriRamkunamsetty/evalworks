import hmac
from collections import defaultdict, deque
from http.cookies import SimpleCookie
from threading import Lock
from time import monotonic
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from redis.asyncio import Redis

from evalworks.auth import CSRF_COOKIE, SESSION_COOKIE
from evalworks.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_windows: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()
_redis: Redis | None = None
_RATE_LIMIT_SCRIPT = (
    "local t = redis.call('TIME'); "
    "local now = (t[1] * 1000) + math.floor(t[2] / 1000); "
    "local window = tonumber(ARGV[1]) * 1000; "
    "redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now - window); "
    "local count = redis.call('ZCARD', KEYS[1]); "
    "if count >= tonumber(ARGV[2]) then return count + 1 end; "
    "redis.call('ZADD', KEYS[1], now, tostring(now) .. ':' .. ARGV[3]); "
    "redis.call('PEXPIRE', KEYS[1], window); "
    "return count + 1"
)
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


def redis_client() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


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
        request_limit = 10 if path == "/api/v1/auth/login" else 120
        if settings.redis_url:
            try:
                count = await redis_client().eval(
                    _RATE_LIMIT_SCRIPT,
                    1,
                    f"evalworks:rate:{bucket_key}",
                    60,
                    request_limit,
                    uuid4().hex,
                )
            except Exception:
                response = JSONResponse(
                    status_code=503, content={"detail": "Rate limit service is unavailable"}
                )
                await response(scope, receive, secure_send)
                return
            if count > request_limit:
                response = JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
                await response(scope, receive, secure_send)
                return
        else:
            now = monotonic()
            with _lock:
                bucket = _windows[bucket_key]
                while bucket and now - bucket[0] > 60:
                    bucket.popleft()
                if len(bucket) >= request_limit:
                    response = JSONResponse(
                        status_code=429, content={"detail": "Rate limit exceeded"}
                    )
                    await response(scope, receive, secure_send)
                    return
                bucket.append(now)
                if len(_windows) > 10_000:
                    for key in [key for key, events in _windows.items() if not events]:
                        _windows.pop(key, None)

        message_index = 0

        async def replay_receive():
            nonlocal message_index
            if message_index < len(messages):
                message = messages[message_index]
                message_index += 1
                return message
            return await receive()

        await self.app(scope, replay_receive, secure_send)

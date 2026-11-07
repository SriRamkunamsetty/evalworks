import hmac
import json
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from evalworks.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_windows: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def require_api_key(provided: str | None = Depends(api_key_header)) -> str:
    if not provided or not hmac.compare_digest(provided, settings.api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return provided


async def request_limits(request: Request, call_next):
    body = await request.body()
    if len(body) > settings.max_request_bytes:
        return JSONResponse(
            status_code=413, content={"detail": "Request body exceeds configured limit"}
        )
    client = request.client.host if request.client else "unknown"
    now = monotonic()
    with _lock:
        bucket = _windows[client]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= 120:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        bucket.append(now)
        if len(_windows) > 10_000:
            for host in [host for host, events in _windows.items() if not events]:
                _windows.pop(host, None)

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    request._receive = receive
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; "
        "img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    )
    return response


def digest_payload(payload: dict) -> str:
    import hashlib

    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

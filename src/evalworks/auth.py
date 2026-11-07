from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from evalworks.config import settings
from evalworks.db import SessionLocal
from evalworks.models import User

SESSION_COOKIE = "ew_session"
CSRF_COOKIE = "ew_csrf"
SESSION_TTL = timedelta(hours=8)
PASSWORD_HASHER = PasswordHash.recommended()
_DUMMY_HASH = PASSWORD_HASHER.hash("not-a-real-user-password")


@dataclass(frozen=True)
class Actor:
    id: str
    workspace_id: str
    email: str
    role: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return PASSWORD_HASHER.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return PASSWORD_HASHER.verify(password, encoded)


def issue_session(user: User) -> tuple[str, str]:
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": user.id,
            "workspace": user.workspace_id,
            "iat": now,
            "exp": now + SESSION_TTL,
            "iss": "evalworks",
        },
        settings.session_secret,
        algorithm="HS256",
    )
    return token, token_urlsafe(32)


def set_session_cookies(response, token: str, csrf: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_session_cookies(response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", secure=settings.cookie_secure, samesite="lax")
    response.delete_cookie(CSRF_COOKIE, path="/", secure=settings.cookie_secure, samesite="lax")


def require_actor(request: Request, db: Annotated[Session, Depends(get_db)]) -> Actor:
    session_token = request.cookies.get(SESSION_COOKIE)
    if session_token:
        try:
            claims = jwt.decode(
                session_token,
                settings.session_secret,
                algorithms=["HS256"],
                issuer="evalworks",
                options={"require": ["sub", "workspace", "exp", "iat", "iss"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        user = db.get(User, claims["sub"])
        if not user or not user.is_active or user.workspace_id != claims["workspace"]:
            raise HTTPException(status_code=401, detail="Account is inactive or unavailable")
        return Actor(user.id, user.workspace_id, user.email, user.role)

    api_key = request.headers.get("X-API-Key")
    if settings.app_env.lower() != "production" and api_key == settings.api_key:
        return Actor("local", "local", "local@localhost", "admin")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sign in is required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_roles(*roles: str):
    def check(actor: Annotated[Actor, Depends(require_actor)]) -> Actor:
        if actor.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role for this action")
        return actor

    return check


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == str(email).strip().casefold()).one_or_none()
    encoded = user.password_hash if user else _DUMMY_HASH
    valid = verify_password(password, encoded)
    return user if user and user.is_active and valid else None

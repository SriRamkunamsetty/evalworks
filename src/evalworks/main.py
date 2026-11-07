from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from evalworks.api import auth_router, router
from evalworks.config import settings, validate_production_settings
from evalworks.db import engine
from evalworks.security import RequestLimitsMiddleware

WEB_ROOT = Path(__file__).parent / "web"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_production_settings()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key", "X-CSRF-Token"],
)
app.add_middleware(RequestLimitsMiddleware)
app.include_router(router)
app.include_router(auth_router)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "service": settings.app_name}


@app.get("/health/ready", include_in_schema=False)
def readiness():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    return {"status": "ready", "service": settings.app_name}


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(WEB_ROOT / "index.html")


@app.get("/app.js", include_in_schema=False)
def javascript():
    return FileResponse(WEB_ROOT / "app.js", media_type="text/javascript")


@app.get("/styles.css", include_in_schema=False)
def styles():
    return FileResponse(WEB_ROOT / "styles.css", media_type="text/css")


@app.get("/chat.css", include_in_schema=False)
def chat_styles():
    return FileResponse(WEB_ROOT / "chat.css", media_type="text/css")

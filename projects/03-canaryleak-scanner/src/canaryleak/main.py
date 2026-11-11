from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from canaryleak.api import router

WEB_ROOT = Path(__file__).parent / "web"

app = FastAPI(
    title="CanaryLeak",
    description="System Prompt Extraction & Canary Token Leakage Scanner for LLMs.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", include_in_schema=False)
def serve_index():
    return FileResponse(WEB_ROOT / "index.html")


@app.get("/styles.css", include_in_schema=False)
def serve_styles():
    return FileResponse(WEB_ROOT / "styles.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def serve_javascript():
    return FileResponse(WEB_ROOT / "app.js", media_type="text/javascript")

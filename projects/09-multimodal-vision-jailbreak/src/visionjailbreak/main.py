import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from visionjailbreak.api import router

app = FastAPI(
    title="Multimodal Vision Jailbreak API",
    description="Typographic Visual Prompt Injection & VLM Safety Testbed",
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

WEB_DIR = Path(__file__).resolve().parent / "web"
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def serve_dashboard():
        index_path = WEB_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"message": "Vision Jailbreak UI is under construction."}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8009"))
    uvicorn.run("visionjailbreak.main:app", host="0.0.0.0", port=port, reload=True)

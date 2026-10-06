from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.routes import auth_router, dashboard_router
from app.api.routes.health import router as health_router
from app.core.config import settings

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title=settings.app_name,
    version="1.1.0",
    description="AION OS professional workspace API",
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix="/api/auth")
app.include_router(dashboard_router, prefix="/api")


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/styles.css")
async def styles() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "styles.css")


@app.get("/app.js")
async def app_js() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "app.js")


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
    }

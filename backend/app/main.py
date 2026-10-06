from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.routes import auth_router, dashboard_router, health_router
from app.core.database import init_db

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="AION OS",
    version="1.3.0",
    description="AION OS professional workspace",
)

app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(dashboard_router, prefix="/api")


@app.on_event("startup")
async def startup_event() -> None:
    init_db()


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
    return {"status": "ok", "app": "AION OS", "environment": "development"}

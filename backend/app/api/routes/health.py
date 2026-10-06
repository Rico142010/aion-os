from fastapi import APIRouter

from app.core.config import settings
from app.core.database import check_database, check_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    db_status = check_database()
    redis_status = check_redis()

    overall_status = "ok" if db_status["ok"] and redis_status["ok"] else "degraded"

    return {
        "status": overall_status,
        "app": settings.app_name,
        "env": settings.app_env,
        "database": db_status,
        "redis": redis_status,
    }


@router.get("/status")
async def status_check() -> dict:
    return {
        "service": settings.app_name,
        "status": "ready",
        "environment": settings.app_env,
    }

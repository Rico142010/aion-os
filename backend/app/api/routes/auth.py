from fastapi import APIRouter
import psycopg2
import redis

from app.core.config import settings

router = APIRouter(tags=["health"])


def _check_database() -> dict:
    try:
        conn = psycopg2.connect(
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            connect_timeout=3,
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        conn.close()
        return {"ok": True, "host": settings.postgres_host, "port": settings.postgres_port, "database": settings.postgres_db}
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "host": settings.postgres_host, "port": settings.postgres_port, "database": settings.postgres_db, "error": str(exc)}


def _check_redis() -> dict:
    client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    try:
        client.ping()
        return {"ok": True, "host": settings.redis_host, "port": settings.redis_port}
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "host": settings.redis_host, "port": settings.redis_port, "error": str(exc)}


@router.get("/health")
async def health_check() -> dict:
    db_status = _check_database()
    redis_status = _check_redis()
    state = "ok" if db_status["ok"] and redis_status["ok"] else "degraded"
    return {
        "status": state,
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

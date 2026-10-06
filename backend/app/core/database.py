import psycopg2
import redis

from app.core.config import settings


def check_database() -> dict:
    try:
        connection = psycopg2.connect(
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            connect_timeout=3,
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        connection.close()
        return {
            "ok": True,
            "host": settings.postgres_host,
            "port": settings.postgres_port,
            "database": settings.postgres_db,
        }
    except Exception as exc:  # pragma: no cover - runtime check only
        return {
            "ok": False,
            "host": settings.postgres_host,
            "port": settings.postgres_port,
            "database": settings.postgres_db,
            "error": str(exc),
        }


def check_redis() -> dict:
    client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    try:
        client.ping()
        return {
            "ok": True,
            "host": settings.redis_host,
            "port": settings.redis_port,
        }
    except Exception as exc:  # pragma: no cover - runtime check only
        return {
            "ok": False,
            "host": settings.redis_host,
            "port": settings.redis_port,
            "error": str(exc),
        }

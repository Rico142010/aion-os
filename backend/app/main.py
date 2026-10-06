from app.api.routes.auth import router as auth_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router

__all__ = ["auth_router", "dashboard_router", "health_router"]

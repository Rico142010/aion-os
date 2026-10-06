from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Project, Task, User


def seed_default_data(db: Session) -> None:
    existing = db.execute(select(User).where(User.email == settings.default_admin_email)).scalar_one_or_none()
    if existing:
        return

    admin = User(
        public_id="u-001",
        name="Administrador",
        email=settings.default_admin_email,
        password=settings.default_admin_password,
        role="admin",
    )
    db.add(admin)
    db.flush()

    project_one = Project(
        public_id="p-001",
        name="AION OS Core",
        description="Plataforma base para IA y automatización.",
        status="active",
        owner_id=admin.id,
    )
    project_two = Project(
        public_id="p-002",
        name="Workspace Studio",
        description="Panel operativo para usuarios y servicios.",
        status="planning",
        owner_id=admin.id,
    )
    db.add_all([project_one, project_two])
    db.flush()

    db.add_all(
        [
            Task(
                public_id="t-001",
                title="Preparar infraestructura base",
                description="Definir la arquitectura inicial del sistema.",
                status="done",
                project_id=project_one.id,
                assignee_id=admin.id,
            ),
            Task(
                public_id="t-002",
                title="Crear autenticación JWT",
                description="Implementar login seguro para usuarios del backend.",
                status="in_progress",
                project_id=project_one.id,
                assignee_id=admin.id,
            ),
            Task(
                public_id="t-003",
                title="Diseñar panel profesional",
                description="Crear tablero con métricas y gestión de tareas.",
                status="todo",
                project_id=project_two.id,
                assignee_id=admin.id,
            ),
        ]
    )
    db.commit()

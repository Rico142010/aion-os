from __future__ import annotations

from typing import Any

USERS: dict[str, dict[str, Any]] = {
    "admin@aion.io": {
        "id": "u-001",
        "name": "Administrador",
        "email": "admin@aion.io",
        "role": "admin",
        "password": "admin123",
        "created_at": "2026-01-01T00:00:00Z",
    }
}

PROJECTS: list[dict[str, Any]] = [
    {
        "id": "p-001",
        "name": "AION OS Core",
        "description": "Plataforma base para IA y automatización.",
        "status": "active",
        "owner": "admin@aion.io",
    },
    {
        "id": "p-002",
        "name": "Workspace Studio",
        "description": "Panel operativo para usuarios y servicios.",
        "status": "planning",
        "owner": "admin@aion.io",
    },
]

TASKS: list[dict[str, Any]] = [
    {
        "id": "t-001",
        "title": "Preparar infraestructura base",
        "description": "Definir la arquitectura inicial del sistema.",
        "status": "done",
        "project_id": "p-001",
        "assignee": "admin@aion.io",
    },
    {
        "id": "t-002",
        "title": "Crear autenticación JWT",
        "description": "Implementar login seguro para usuarios del backend.",
        "status": "in_progress",
        "project_id": "p-001",
        "assignee": "admin@aion.io",
    },
    {
        "id": "t-003",
        "title": "Diseñar panel profesional",
        "description": "Crear tablero con métricas y gestión de tareas.",
        "status": "todo",
        "project_id": "p-002",
        "assignee": "admin@aion.io",
    },
]

users = USERS
projects = PROJECTS
tasks = TASKS

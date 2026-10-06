from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.core.store import projects, tasks

router = APIRouter(tags=["dashboard"])


class ProjectInput(BaseModel):
    name: str = Field(..., min_length=2)
    description: str = Field(default="")
    status: str = Field(default="planning")


class TaskInput(BaseModel):
    title: str = Field(..., min_length=2)
    description: str = Field(default="")
    status: str = Field(default="todo")
    project_id: str = Field(...)


@router.get("/dashboard/overview")
async def dashboard_overview(current_user: dict = Depends(get_current_user)) -> dict[str, Any]:
    total_projects = len(projects)
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task["status"] == "done")
    progress = round((completed_tasks / total_tasks) * 100, 1) if total_tasks else 0

    return {
        "user": {
            "name": current_user["name"],
            "email": current_user["email"],
            "role": current_user["role"],
        },
        "stats": {
            "projects": total_projects,
            "tasks": total_tasks,
            "completed": completed_tasks,
            "progress": progress,
        },
        "projects": projects,
        "tasks": tasks,
    }


@router.get("/projects")
async def list_projects(current_user: dict = Depends(get_current_user)):
    return projects


@router.post("/projects")
async def create_project(payload: ProjectInput, current_user: dict = Depends(get_current_user)):
    project = {
        "id": f"p-{len(projects) + 1:03d}",
        "name": payload.name,
        "description": payload.description,
        "status": payload.status,
        "owner": current_user["email"],
    }
    projects.append(project)
    return project


@router.get("/tasks")
async def list_tasks(current_user: dict = Depends(get_current_user)):
    return tasks


@router.post("/tasks")
async def create_task(payload: TaskInput, current_user: dict = Depends(get_current_user)):
    if not any(project["id"] == payload.project_id for project in projects):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")

    task = {
        "id": f"t-{len(tasks) + 1:03d}",
        "title": payload.title,
        "description": payload.description,
        "status": payload.status,
        "project_id": payload.project_id,
        "assignee": current_user["email"],
    }
    tasks.append(task)
    return task

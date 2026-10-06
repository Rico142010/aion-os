from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db, get_all_projects, get_all_tasks, get_project_by_id
from app.core.security import get_current_user
from app.models import Project, Task, User

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
async def dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    projects = get_all_projects(db)
    tasks = get_all_tasks(db)
    total_projects = len(projects)
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.status == "done")
    progress = round((completed_tasks / total_tasks) * 100, 1) if total_tasks else 0

    return {
        "user": {
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
        },
        "stats": {
            "projects": total_projects,
            "tasks": total_tasks,
            "completed": completed_tasks,
            "progress": progress,
        },
        "projects": [
            {
                "id": project.public_id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "owner": current_user.email,
            }
            for project in projects
        ],
        "tasks": [
            {
                "id": task.public_id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "project_id": task.project.public_id,
                "assignee": task.assignee_user.email,
            }
            for task in tasks
        ],
    }


@router.get("/projects")
async def list_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [
        {
            "id": project.public_id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "owner": project.owner_user.email,
        }
        for project in get_all_projects(db)
    ]


@router.post("/projects")
async def create_project(
    payload: ProjectInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = Project(
        public_id=f"p-{db.query(Project).count() + 1:03d}",
        name=payload.name,
        description=payload.description,
        status=payload.status,
        owner_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {
        "id": project.public_id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "owner": current_user.email,
    }


@router.get("/tasks")
async def list_tasks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [
        {
            "id": task.public_id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "project_id": task.project.public_id,
            "assignee": task.assignee_user.email,
        }
        for task in get_all_tasks(db)
    ]


@router.post("/tasks")
async def create_task(
    payload: TaskInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project_by_id(db, payload.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")

    task = Task(
        public_id=f"t-{db.query(Task).count() + 1:03d}",
        title=payload.title,
        description=payload.description,
        status=payload.status,
        project_id=project.id,
        assignee_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {
        "id": task.public_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "project_id": project.public_id,
        "assignee": current_user.email,
    }

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.models import Base, Project, Task, User

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_default_data(db: Session) -> None:
    existing_admin = db.execute(select(User).where(User.email == settings.default_admin_email)).scalar_one_or_none()
    if existing_admin:
        return

    admin = User(
        public_id="u-001",
        name="Administrador",
        email=settings.default_admin_email,
        password=hash_password(settings.default_admin_password),
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


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_data(db)
    finally:
        db.close()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_project_by_id(db: Session, project_id: str) -> Project | None:
    return db.execute(select(Project).where(Project.public_id == project_id)).scalar_one_or_none()


def get_all_projects(db: Session) -> list[Project]:
    return db.execute(select(Project)).scalars().all()


def get_all_tasks(db: Session) -> list[Task]:
    return db.execute(select(Task)).scalars().all()

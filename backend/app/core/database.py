from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.security import seed_default_data
from app.models import Base, Project, Task, User

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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

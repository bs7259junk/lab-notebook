from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Project


def get_project(db: Session, project_id: uuid.UUID) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()


def get_project_by_code(db: Session, code: str) -> Optional[Project]:
    return db.query(Project).filter(Project.project_code == code).first()


def list_projects(
    db: Session,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Project]:
    q = db.query(Project)
    if status:
        q = q.filter(Project.status == status)
    return q.offset(skip).limit(limit).all()


def create_project(
    db: Session,
    project_code: str,
    title: str,
    description: Optional[str],
    created_by: uuid.UUID,
    status: str = "active",
) -> Project:
    project = Project(
        project_code=project_code,
        title=title,
        description=description,
        created_by=created_by,
        status=status,
    )
    db.add(project)
    db.flush()
    return project

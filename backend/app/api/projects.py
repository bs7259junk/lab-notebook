from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user, require_roles
from app.db import get_db
from app.models.models import User
from app.repositories.experiment_repo import list_experiments
from app.repositories.project_repo import (
    create_project,
    get_project,
    get_project_by_code,
    list_projects,
)
from app.schemas.schemas import ExperimentOut, ProjectCreate, ProjectOut, ProjectUpdate
from app.services.audit_service import log_action

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=List[ProjectOut])
def list_all_projects(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list:
    return list_projects(db, status=status, skip=skip, limit=limit)


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_new_project(
    body: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "scientist")),
) -> object:
    if get_project_by_code(db, body.project_code):
        raise HTTPException(status_code=409, detail="Project code already exists")

    project = create_project(
        db,
        project_code=body.project_code,
        title=body.title,
        description=body.description,
        created_by=current_user.id,
        status=body.status,
    )
    log_action(
        db=db,
        entity_type="project",
        entity_id=str(project.id),
        action="created",
        actor=current_user,
        new_value={"project_code": project.project_code, "title": project.title},
        request=request,
    )
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_one_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> object:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "scientist")),
) -> object:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if body.title is not None:
        project.title = body.title
    if body.description is not None:
        project.description = body.description
    if body.status is not None:
        project.status = body.status

    log_action(
        db=db,
        entity_type="project",
        entity_id=str(project.id),
        action="updated",
        actor=current_user,
        new_value=body.model_dump(exclude_none=True),
        request=request,
    )
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}/experiments", response_model=List[ExperimentOut])
def get_project_experiments(
    project_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return list_experiments(db, project_id=project_id, skip=skip, limit=limit)

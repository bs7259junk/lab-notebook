from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.models.models import Experiment, User
from app.repositories.experiment_repo import (
    create_experiment as _create,
    get_experiment,
)
from app.services.audit_service import log_action

# ---------------------------------------------------------------------------
# Valid status machine
# ---------------------------------------------------------------------------

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"in_progress"},
    "in_progress": {"completed"},
    "completed": {"under_review"},
    "under_review": {"approved", "returned"},
    "approved": {"archived"},
    "archived": set(),
    "returned": {"in_progress"},  # allow re-submission after revision
}

# Statuses where further edits are blocked
LOCKED_STATUSES = {"approved", "archived"}


def create_experiment(
    db: Session,
    title: str,
    purpose: str,
    project_id,
    barcode: Optional[str],
    current_user: User,
    request: Optional[Request] = None,
) -> Experiment:
    exp = _create(
        db=db,
        title=title,
        purpose=purpose,
        project_id=project_id,
        owner_id=current_user.id,
        barcode=barcode,
    )
    log_action(
        db=db,
        entity_type="experiment",
        entity_id=str(exp.id),
        action="created",
        actor=current_user,
        new_value={
            "experiment_id": exp.experiment_id,
            "title": exp.title,
            "project_id": str(exp.project_id),
            "status": exp.status,
        },
        request=request,
    )
    return exp


def update_experiment(
    db: Session,
    exp_id,
    data: dict,
    current_user: User,
    request: Optional[Request] = None,
) -> Experiment:
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    if exp.status in LOCKED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Experiment is {exp.status} and cannot be modified",
        )

    old_values = {k: getattr(exp, k) for k in data if hasattr(exp, k)}

    for field, value in data.items():
        if value is not None and hasattr(exp, field):
            setattr(exp, field, value)

    log_action(
        db=db,
        entity_type="experiment",
        entity_id=str(exp.id),
        action="updated",
        actor=current_user,
        old_value={k: str(v) if v is not None else None for k, v in old_values.items()},
        new_value={k: str(v) if v is not None else None for k, v in data.items()},
        request=request,
    )
    return exp


def transition_status(
    db: Session,
    exp_id,
    new_status: str,
    current_user: User,
    request: Optional[Request] = None,
) -> Experiment:
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    allowed = ALLOWED_TRANSITIONS.get(exp.status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Cannot transition from '{exp.status}' to '{new_status}'. "
                f"Allowed transitions: {sorted(allowed) or 'none'}"
            ),
        )

    old_status = exp.status
    exp.status = new_status

    if new_status == "completed":
        exp.completed_at = datetime.now(timezone.utc)

    log_action(
        db=db,
        entity_type="experiment",
        entity_id=str(exp.id),
        action="status_changed",
        actor=current_user,
        old_value={"status": old_status},
        new_value={"status": new_status},
        request=request,
    )
    return exp

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.db import get_db
from app.models.models import LabEntry, User
from app.models.models import LAB_ENTRY_SECTIONS
from app.repositories.experiment_repo import get_experiment
from app.schemas.schemas import LabEntryOut, LabEntryUpdate
from app.services.audit_service import log_action

router = APIRouter(tags=["entries"])


@router.get("/experiments/{exp_id}/entries", response_model=List[LabEntryOut])
def list_entries(
    exp_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list:
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp.entries


@router.put("/experiments/{exp_id}/entries/{section}", response_model=LabEntryOut)
def upsert_entry(
    exp_id: uuid.UUID,
    section: str,
    body: LabEntryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> LabEntry:
    if section not in LAB_ENTRY_SECTIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid section '{section}'. Valid: {sorted(LAB_ENTRY_SECTIONS)}",
        )

    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    entry = (
        db.query(LabEntry)
        .filter(LabEntry.experiment_id == exp_id, LabEntry.section == section)
        .first()
    )

    if entry:
        old_content = entry.content
        entry.content = body.content
        entry.version += 1
        action = "updated"
        old_val = {"content": old_content[:200] + "..." if len(old_content) > 200 else old_content}
    else:
        entry = LabEntry(
            experiment_id=exp_id,
            section=section,
            content=body.content,
            created_by=current_user.id,
        )
        db.add(entry)
        db.flush()
        action = "created"
        old_val = None

    log_action(
        db=db,
        entity_type="experiment",
        entity_id=str(exp_id),
        action=action,
        actor=current_user,
        old_value=old_val,
        new_value={"section": section, "version": entry.version},
        request=request,
    )
    db.commit()
    db.refresh(entry)
    return entry


@router.get(
    "/experiments/{exp_id}/entries/{section}/history",
    response_model=List[LabEntryOut],
)
def entry_history(
    exp_id: uuid.UUID,
    section: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list:
    """
    Returns the current version of the entry (history is tracked via audit log).
    For full version history query GET /audit?entity_type=experiment&entity_id={exp_id}.
    """
    entry = (
        db.query(LabEntry)
        .filter(LabEntry.experiment_id == exp_id, LabEntry.section == section)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return [entry]

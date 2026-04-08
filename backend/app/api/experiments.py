from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.db import get_db
from app.models.models import Experiment, ExperimentParticipant, User
from app.repositories.experiment_repo import get_experiment, list_experiments
from app.schemas.schemas import (
    ExperimentCreate,
    ExperimentDetail,
    ExperimentOut,
    ExperimentParticipantOut,
    ExperimentUpdate,
    ParticipantAdd,
    StatusTransition,
)
from app.services.audit_service import log_action
from app.services.experiment_service import (
    create_experiment,
    transition_status,
    update_experiment,
)

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("", response_model=List[ExperimentOut])
def list_all_experiments(
    project_id: Optional[uuid.UUID] = None,
    owner_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    barcode: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list:
    return list_experiments(
        db,
        project_id=project_id,
        owner_id=owner_id,
        status=status,
        search=search,
        date_from=date_from,
        date_to=date_to,
        barcode=barcode,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=ExperimentOut, status_code=status.HTTP_201_CREATED)
def create_new_experiment(
    body: ExperimentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Experiment:
    from app.repositories.project_repo import get_project

    if not get_project(db, body.project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    exp = create_experiment(
        db=db,
        title=body.title,
        purpose=body.purpose,
        project_id=body.project_id,
        barcode=body.barcode,
        current_user=current_user,
        request=request,
    )
    db.commit()
    db.refresh(exp)
    return exp


@router.get("/{exp_id}", response_model=ExperimentDetail)
def get_one_experiment(
    exp_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Experiment:
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@router.patch("/{exp_id}", response_model=ExperimentOut)
def update_one_experiment(
    exp_id: uuid.UUID,
    body: ExperimentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Experiment:
    exp = update_experiment(
        db=db,
        exp_id=exp_id,
        data=body.model_dump(exclude_none=True),
        current_user=current_user,
        request=request,
    )
    db.commit()
    db.refresh(exp)
    return exp


@router.post("/{exp_id}/status", response_model=ExperimentOut)
def change_status(
    exp_id: uuid.UUID,
    body: StatusTransition,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Experiment:
    exp = transition_status(
        db=db,
        exp_id=exp_id,
        new_status=body.new_status,
        current_user=current_user,
        request=request,
    )
    db.commit()
    db.refresh(exp)
    return exp


@router.get("/{exp_id}/participants", response_model=List[ExperimentParticipantOut])
def list_participants(
    exp_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list:
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp.participants


@router.post(
    "/{exp_id}/participants",
    response_model=ExperimentParticipantOut,
    status_code=status.HTTP_201_CREATED,
)
def add_participant(
    exp_id: uuid.UUID,
    body: ParticipantAdd,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ExperimentParticipant:
    from app.repositories.user_repo import get_user_by_id

    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    user = get_user_by_id(db, body.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check not already a participant
    existing = (
        db.query(ExperimentParticipant)
        .filter(
            ExperimentParticipant.experiment_id == exp_id,
            ExperimentParticipant.user_id == body.user_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="User is already a participant")

    participant = ExperimentParticipant(
        experiment_id=exp_id,
        user_id=body.user_id,
        role=body.role,
    )
    db.add(participant)
    log_action(
        db=db,
        entity_type="experiment",
        entity_id=str(exp_id),
        action="updated",
        actor=current_user,
        new_value={"participant_added": str(body.user_id), "role": body.role},
        request=request,
    )
    db.commit()
    db.refresh(participant)
    return participant


@router.delete("/{exp_id}/participants/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_participant(
    exp_id: uuid.UUID,
    user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    participant = (
        db.query(ExperimentParticipant)
        .filter(
            ExperimentParticipant.experiment_id == exp_id,
            ExperimentParticipant.user_id == user_id,
        )
        .first()
    )
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    db.delete(participant)
    log_action(
        db=db,
        entity_type="experiment",
        entity_id=str(exp_id),
        action="updated",
        actor=current_user,
        new_value={"participant_removed": str(user_id)},
        request=request,
    )
    db.commit()

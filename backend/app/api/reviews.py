from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.db import get_db
from app.models.models import Review, Signature, User
from app.repositories.experiment_repo import get_experiment
from app.schemas.schemas import ReviewCreate, ReviewOut, ReviewUpdate, SignatureCreate, SignatureOut
from app.services.review_service import add_signature, complete_review, submit_for_review

router = APIRouter(tags=["reviews"])


@router.get("/experiments/{exp_id}/reviews", response_model=List[ReviewOut])
def list_reviews(
    exp_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list:
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp.reviews


@router.post(
    "/experiments/{exp_id}/reviews",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    exp_id: uuid.UUID,
    body: ReviewCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Review:
    review = submit_for_review(
        db=db,
        exp_id=exp_id,
        reviewer_id=body.reviewer_id,
        current_user=current_user,
        request=request,
    )
    db.commit()
    db.refresh(review)
    return review


@router.patch("/reviews/{review_id}", response_model=ReviewOut)
def update_review(
    review_id: uuid.UUID,
    body: ReviewUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Review:
    review = complete_review(
        db=db,
        review_id=review_id,
        review_status=body.status,
        comments=body.comments,
        current_user=current_user,
        request=request,
    )
    db.commit()
    db.refresh(review)
    return review


@router.post(
    "/experiments/{exp_id}/sign",
    response_model=SignatureOut,
    status_code=status.HTTP_201_CREATED,
)
def sign_experiment(
    exp_id: uuid.UUID,
    body: SignatureCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Signature:
    sig = add_signature(
        db=db,
        exp_id=exp_id,
        sig_type=body.signature_type,
        meaning=body.meaning,
        current_user=current_user,
        request=request,
    )
    db.commit()
    db.refresh(sig)
    return sig


@router.get("/experiments/{exp_id}/signatures", response_model=List[SignatureOut])
def list_signatures(
    exp_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list:
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp.signatures

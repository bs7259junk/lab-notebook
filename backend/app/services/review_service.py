from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.models.models import Experiment, Review, Signature, User
from app.repositories.experiment_repo import get_experiment
from app.services.audit_service import log_action


def submit_for_review(
    db: Session,
    exp_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    current_user: User,
    request: Optional[Request] = None,
) -> Review:
    exp: Optional[Experiment] = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    if exp.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only completed experiments can be submitted for review",
        )

    # Enforce reviewer != owner
    if reviewer_id == exp.owner_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The reviewer cannot be the experiment owner",
        )

    # Transition experiment status
    exp.status = "under_review"

    review = Review(
        experiment_id=exp_id,
        reviewer_id=reviewer_id,
        status="pending",
    )
    db.add(review)
    db.flush()

    log_action(
        db=db,
        entity_type="review",
        entity_id=str(review.id),
        action="created",
        actor=current_user,
        new_value={
            "experiment_id": str(exp_id),
            "reviewer_id": str(reviewer_id),
            "status": "pending",
        },
        request=request,
    )
    return review


def complete_review(
    db: Session,
    review_id: uuid.UUID,
    review_status: str,
    comments: Optional[str],
    current_user: User,
    request: Optional[Request] = None,
) -> Review:
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if review.reviewer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned reviewer can complete this review",
        )

    if review_status not in ("approved", "returned", "in_review"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="review_status must be approved, returned, or in_review",
        )

    old_status = review.status
    review.status = review_status
    review.comments = comments
    if review_status in ("approved", "returned"):
        review.completed_at = datetime.now(timezone.utc)

        # Transition experiment accordingly
        exp = get_experiment(db, review.experiment_id)
        if exp:
            exp.status = review_status  # approved or returned

    log_action(
        db=db,
        entity_type="review",
        entity_id=str(review.id),
        action="reviewed",
        actor=current_user,
        old_value={"status": old_status},
        new_value={"status": review_status, "comments": comments},
        request=request,
    )
    return review


def add_signature(
    db: Session,
    exp_id: uuid.UUID,
    sig_type: str,
    meaning: str,
    current_user: User,
    request: Optional[Request] = None,
) -> Signature:
    exp: Optional[Experiment] = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    # Enforce reviewer != owner for review-type signatures
    if sig_type == "review" and current_user.id == exp.owner_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The reviewer cannot be the experiment owner",
        )

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    if request:
        fwd = request.headers.get("x-forwarded-for")
        ip_address = fwd.split(",")[0].strip() if fwd else (
            request.client.host if request.client else None
        )
        user_agent = request.headers.get("user-agent")

    sig = Signature(
        experiment_id=exp_id,
        signer_id=current_user.id,
        signature_type=sig_type,
        meaning=meaning,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(sig)
    db.flush()

    log_action(
        db=db,
        entity_type="signature",
        entity_id=str(sig.id),
        action="signed",
        actor=current_user,
        new_value={
            "experiment_id": str(exp_id),
            "signature_type": sig_type,
            "meaning": meaning,
        },
        request=request,
    )
    return sig

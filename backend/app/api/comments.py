from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.db import get_db
from app.models.models import Comment, User
from app.repositories.experiment_repo import get_experiment
from app.schemas.schemas import CommentCreate, CommentOut, CommentUpdate
from app.services.audit_service import log_action

router = APIRouter(tags=["comments"])


@router.get("/experiments/{exp_id}/comments", response_model=List[CommentOut])
def list_comments(
    exp_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list:
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return [c for c in exp.comments if not c.is_deleted]


@router.post(
    "/experiments/{exp_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    exp_id: uuid.UUID,
    body: CommentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Comment:
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    comment = Comment(
        experiment_id=exp_id,
        author_id=current_user.id,
        comment_type=body.comment_type,
        content=body.content,
    )
    db.add(comment)
    db.flush()
    log_action(
        db=db,
        entity_type="comment",
        entity_id=str(comment.id),
        action="created",
        actor=current_user,
        new_value={"experiment_id": str(exp_id), "type": body.comment_type},
        request=request,
    )
    db.commit()
    db.refresh(comment)
    return comment


@router.patch("/comments/{comment_id}", response_model=CommentOut)
def update_comment(
    comment_id: uuid.UUID,
    body: CommentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Comment:
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.is_deleted == False).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id:
        # Only admins can edit other users' comments
        user_roles = {r.role for r in current_user.roles}
        if "admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Not authorized to edit this comment")

    old_content = comment.content
    comment.content = body.content
    log_action(
        db=db,
        entity_type="comment",
        entity_id=str(comment.id),
        action="updated",
        actor=current_user,
        old_value={"content": old_content},
        new_value={"content": body.content},
        request=request,
    )
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id:
        user_roles = {r.role for r in current_user.roles}
        if "admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    comment.is_deleted = True
    log_action(
        db=db,
        entity_type="comment",
        entity_id=str(comment.id),
        action="deleted",
        actor=current_user,
        old_value={"experiment_id": str(comment.experiment_id)},
        request=request,
    )
    db.commit()

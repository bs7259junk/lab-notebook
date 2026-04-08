from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user, require_roles
from app.auth.passwords import hash_password
from app.db import get_db
from app.models.models import User
from app.repositories.user_repo import (
    add_role,
    create_user,
    get_user_by_id,
    list_users,
    remove_role,
)
from app.schemas.schemas import RoleAssign, UserCreate, UserUpdate, UserWithRoles
from app.services.audit_service import log_action

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserWithRoles])
def list_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> list[User]:
    return list_users(db, skip=skip, limit=limit)


@router.post("", response_model=UserWithRoles, status_code=status.HTTP_201_CREATED)
def create_new_user(
    body: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> User:
    from app.repositories.user_repo import get_user_by_email, get_user_by_username

    if get_user_by_username(db, body.username):
        raise HTTPException(status_code=409, detail="Username already exists")
    if get_user_by_email(db, body.email):
        raise HTTPException(status_code=409, detail="Email already exists")

    user = create_user(
        db,
        username=body.username,
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
    )
    for role in body.roles:
        add_role(db, user, role, assigned_by=current_user.id)

    log_action(
        db=db,
        entity_type="user",
        entity_id=str(user.id),
        action="created",
        actor=current_user,
        new_value={"username": user.username, "email": user.email, "roles": body.roles},
        request=request,
    )
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserWithRoles)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> User:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserWithRoles)
def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> User:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.email is not None:
        user.email = body.email
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.password is not None:
        user.hashed_password = hash_password(body.password)

    log_action(
        db=db,
        entity_type="user",
        entity_id=str(user.id),
        action="updated",
        actor=current_user,
        new_value=body.model_dump(exclude_none=True, exclude={"password"}),
        request=request,
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/roles", response_model=UserWithRoles)
def assign_role(
    user_id: uuid.UUID,
    body: RoleAssign,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> User:
    from app.models.models import VALID_ROLES

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"Invalid role. Valid: {VALID_ROLES}")

    add_role(db, user, body.role, assigned_by=current_user.id)
    log_action(
        db=db,
        entity_type="user",
        entity_id=str(user.id),
        action="updated",
        actor=current_user,
        new_value={"role_assigned": body.role},
        request=request,
    )
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}/roles/{role}", response_model=UserWithRoles)
def remove_user_role(
    user_id: uuid.UUID,
    role: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> User:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    removed = remove_role(db, user, role)
    if not removed:
        raise HTTPException(status_code=404, detail=f"User does not have role '{role}'")

    log_action(
        db=db,
        entity_type="user",
        entity_id=str(user.id),
        action="updated",
        actor=current_user,
        new_value={"role_removed": role},
        request=request,
    )
    db.commit()
    db.refresh(user)
    return user

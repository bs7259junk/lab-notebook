from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import User, UserRole


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return db.query(User).offset(skip).limit(limit).all()


def create_user(
    db: Session,
    username: str,
    email: str,
    full_name: str,
    hashed_password: str,
) -> User:
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
    )
    db.add(user)
    db.flush()
    return user


def add_role(
    db: Session,
    user: User,
    role: str,
    assigned_by: Optional[uuid.UUID] = None,
) -> UserRole:
    existing = (
        db.query(UserRole)
        .filter(UserRole.user_id == user.id, UserRole.role == role)
        .first()
    )
    if existing:
        return existing
    user_role = UserRole(user_id=user.id, role=role, assigned_by=assigned_by)
    db.add(user_role)
    db.flush()
    return user_role


def remove_role(db: Session, user: User, role: str) -> bool:
    user_role = (
        db.query(UserRole)
        .filter(UserRole.user_id == user.id, UserRole.role == role)
        .first()
    )
    if user_role:
        db.delete(user_role)
        db.flush()
        return True
    return False

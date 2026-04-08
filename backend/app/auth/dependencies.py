from __future__ import annotations

from typing import Callable

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.models import User

# ---------------------------------------------------------------------------
# Auth bypassed for testing — returns first admin user from DB
# ---------------------------------------------------------------------------


def get_current_user(db: Session = Depends(get_db)) -> User:
    user = db.query(User).first()
    if user is None:
        # Fallback: create an in-memory stub so endpoints don't crash
        user = User()
        user.id = "00000000-0000-0000-0000-000000000000"
        user.username = "dev"
        user.full_name = "Dev User"
        user.is_active = True
        user.roles = []
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


def require_roles(*roles: str) -> Callable:
    def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        return current_user
    return dependency

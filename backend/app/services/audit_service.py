from __future__ import annotations

from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.models import AuditLog, User
from app.repositories.audit_repo import create_audit_log


def _get_ip(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    # Respect X-Forwarded-For when behind a proxy
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def log_action(
    db: Session,
    entity_type: str,
    entity_id: str,
    action: str,
    actor: Optional[User],
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    """
    Create an immutable audit log entry.

    Call this from every service method that creates or modifies data.
    The AuditLog table must NEVER be updated or deleted.
    """
    return create_audit_log(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_id=actor.id if actor else None,
        actor_username=actor.username if actor else None,
        old_value=old_value,
        new_value=new_value,
        ip_address=_get_ip(request),
    )

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.models import AuditLog


def create_audit_log(
    db: Session,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_id: Optional[uuid.UUID],
    actor_username: Optional[str],
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Append a new immutable audit log entry.
    NEVER update or delete rows in this table.
    """
    log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_id=actor_id,
        actor_username=actor_username,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
    )
    db.add(log)
    db.flush()
    return log


def query_audit_logs(
    db: Session,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    actor_id: Optional[uuid.UUID] = None,
    action: Optional[str] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[int, List[AuditLog]]:
    q = db.query(AuditLog)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    if actor_id:
        q = q.filter(AuditLog.actor_id == actor_id)
    if action:
        q = q.filter(AuditLog.action == action)
    if from_dt:
        q = q.filter(AuditLog.timestamp >= from_dt)
    if to_dt:
        q = q.filter(AuditLog.timestamp <= to_dt)
    total = q.count()
    items = q.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return total, items

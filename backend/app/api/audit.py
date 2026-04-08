from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.db import get_db
from app.models.models import User
from app.repositories.audit_repo import query_audit_logs
from app.schemas.schemas import PaginatedAuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=PaginatedAuditLog)
def get_audit_log(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    actor_id: Optional[uuid.UUID] = None,
    action: Optional[str] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "reviewer")),
) -> PaginatedAuditLog:
    skip = (page - 1) * page_size
    total, items = query_audit_logs(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        action=action,
        from_dt=from_dt,
        to_dt=to_dt,
        skip=skip,
        limit=page_size,
    )
    return PaginatedAuditLog(total=total, page=page, page_size=page_size, items=items)

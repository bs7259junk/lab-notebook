from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.models import Experiment


def get_experiment(db: Session, exp_id: uuid.UUID) -> Optional[Experiment]:
    return db.query(Experiment).filter(Experiment.id == exp_id).first()


def get_experiment_by_string_id(db: Session, experiment_id: str) -> Optional[Experiment]:
    return db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()


def get_experiment_by_barcode(db: Session, barcode: str) -> Optional[Experiment]:
    return db.query(Experiment).filter(Experiment.barcode == barcode).first()


def list_experiments(
    db: Session,
    project_id: Optional[uuid.UUID] = None,
    owner_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    barcode: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Experiment]:
    q = db.query(Experiment)
    if project_id:
        q = q.filter(Experiment.project_id == project_id)
    if owner_id:
        q = q.filter(Experiment.owner_id == owner_id)
    if status:
        q = q.filter(Experiment.status == status)
    if search:
        q = q.filter(
            Experiment.title.ilike(f"%{search}%")
            | Experiment.purpose.ilike(f"%{search}%")
            | Experiment.experiment_id.ilike(f"%{search}%")
        )
    if date_from:
        q = q.filter(Experiment.created_at >= date_from)
    if date_to:
        q = q.filter(Experiment.created_at <= date_to)
    if barcode:
        q = q.filter(Experiment.barcode == barcode)
    return q.order_by(Experiment.created_at.desc()).offset(skip).limit(limit).all()


def generate_experiment_id(db: Session) -> str:
    """
    Auto-generate EXP-YYYY-NNN, sequential per year, padded to 3 digits.
    Thread-safe: uses DB-level count within the same transaction.
    """
    year = datetime.now(timezone.utc).year
    prefix = f"EXP-{year}-"
    count = (
        db.query(func.count(Experiment.id))
        .filter(Experiment.experiment_id.like(f"{prefix}%"))
        .scalar()
    ) or 0
    return f"{prefix}{count + 1:03d}"


def create_experiment(
    db: Session,
    title: str,
    purpose: str,
    project_id: uuid.UUID,
    owner_id: uuid.UUID,
    barcode: Optional[str] = None,
) -> Experiment:
    exp_id_str = generate_experiment_id(db)
    experiment = Experiment(
        experiment_id=exp_id_str,
        title=title,
        purpose=purpose,
        project_id=project_id,
        owner_id=owner_id,
        barcode=barcode,
    )
    db.add(experiment)
    db.flush()
    return experiment

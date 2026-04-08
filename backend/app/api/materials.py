from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.db import get_db
from app.models.models import ExperimentMaterial, Material, User
from app.repositories.experiment_repo import get_experiment
from app.schemas.schemas import (
    ExperimentMaterialCreate,
    ExperimentMaterialOut,
    MaterialCreate,
    MaterialOut,
)
from app.services.audit_service import log_action

router = APIRouter(tags=["materials"])


# ---------------------------------------------------------------------------
# Material catalog
# ---------------------------------------------------------------------------


@router.get("/materials", response_model=List[MaterialOut])
def list_materials(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list:
    q = db.query(Material)
    if search:
        q = q.filter(
            Material.name.ilike(f"%{search}%")
            | Material.catalog_number.ilike(f"%{search}%")
            | Material.vendor.ilike(f"%{search}%")
        )
    return q.offset(skip).limit(limit).all()


@router.post("/materials", response_model=MaterialOut, status_code=status.HTTP_201_CREATED)
def create_material(
    body: MaterialCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Material:
    material = Material(**body.model_dump())
    db.add(material)
    db.flush()
    log_action(
        db=db,
        entity_type="material",
        entity_id=str(material.id),
        action="created",
        actor=current_user,
        new_value={"name": material.name, "catalog_number": material.catalog_number},
        request=request,
    )
    db.commit()
    db.refresh(material)
    return material


# ---------------------------------------------------------------------------
# Experiment material usage
# ---------------------------------------------------------------------------


@router.get(
    "/experiments/{exp_id}/materials", response_model=List[ExperimentMaterialOut]
)
def list_experiment_materials(
    exp_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list:
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp.materials


@router.post(
    "/experiments/{exp_id}/materials",
    response_model=ExperimentMaterialOut,
    status_code=status.HTTP_201_CREATED,
)
def add_experiment_material(
    exp_id: uuid.UUID,
    body: ExperimentMaterialCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ExperimentMaterial:
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    em = ExperimentMaterial(
        experiment_id=exp_id,
        added_by=current_user.id,
        **body.model_dump(),
    )
    db.add(em)
    db.flush()
    log_action(
        db=db,
        entity_type="experiment",
        entity_id=str(exp_id),
        action="updated",
        actor=current_user,
        new_value={"material_added": body.material_name, "lot": body.lot_number},
        request=request,
    )
    db.commit()
    db.refresh(em)
    return em


@router.delete(
    "/experiments/{exp_id}/materials/{usage_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_experiment_material(
    exp_id: uuid.UUID,
    usage_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    em = (
        db.query(ExperimentMaterial)
        .filter(
            ExperimentMaterial.id == usage_id,
            ExperimentMaterial.experiment_id == exp_id,
        )
        .first()
    )
    if not em:
        raise HTTPException(status_code=404, detail="Material usage not found")

    log_action(
        db=db,
        entity_type="experiment",
        entity_id=str(exp_id),
        action="updated",
        actor=current_user,
        old_value={"material_removed": em.material_name},
        request=request,
    )
    db.delete(em)
    db.commit()

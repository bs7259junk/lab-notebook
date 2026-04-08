from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.db import get_db
from app.models.models import ExperimentMaterial, Material, User
from app.repositories.experiment_repo import get_experiment_by_barcode

router = APIRouter(prefix="/barcodes", tags=["barcodes"])


@router.get("/lookup")
def barcode_lookup(
    barcode: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> dict:
    """
    Look up an experiment or material by barcode.
    Returns entity type and basic info, or 404 if not found.
    """
    # Check experiments first
    exp = get_experiment_by_barcode(db, barcode)
    if exp:
        return {
            "type": "experiment",
            "id": str(exp.id),
            "experiment_id": exp.experiment_id,
            "title": exp.title,
            "status": exp.status,
            "barcode": exp.barcode,
        }

    # Check material catalog
    material = db.query(Material).filter(Material.barcode == barcode).first()
    if material:
        return {
            "type": "material",
            "id": str(material.id),
            "name": material.name,
            "catalog_number": material.catalog_number,
            "vendor": material.vendor,
            "barcode": material.barcode,
        }

    # Check experiment material usage
    em = db.query(ExperimentMaterial).filter(ExperimentMaterial.barcode == barcode).first()
    if em:
        return {
            "type": "experiment_material",
            "id": str(em.id),
            "experiment_id": str(em.experiment_id),
            "material_name": em.material_name,
            "lot_number": em.lot_number,
            "barcode": em.barcode,
        }

    raise HTTPException(status_code=404, detail=f"No entity found with barcode '{barcode}'")

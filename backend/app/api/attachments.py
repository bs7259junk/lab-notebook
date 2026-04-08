from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.db import get_db
from app.models.models import Attachment, User
from app.repositories.experiment_repo import get_experiment
from app.schemas.schemas import AttachmentOut
from app.services.attachment_service import delete_attachment, save_attachment
from app.storage.local import storage

router = APIRouter(tags=["attachments"])


@router.get("/experiments/{exp_id}/attachments", response_model=List[AttachmentOut])
def list_attachments(
    exp_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list:
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp.attachments


@router.post("/experiments/{exp_id}/attachments", response_model=AttachmentOut, status_code=201)
async def upload_attachment(
    exp_id: uuid.UUID,
    file: UploadFile,
    request: Request,
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Attachment:
    attachment = await save_attachment(
        db=db,
        exp_id=exp_id,
        file=file,
        description=description,
        current_user=current_user,
        request=request,
    )
    db.commit()
    db.refresh(attachment)
    return attachment


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Response:
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    if not storage.exists(attachment.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    data = storage.load(attachment.file_path)
    return Response(
        content=data,
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{attachment.filename}"',
            "Content-Length": str(len(data)),
        },
    )


@router.delete("/attachments/{attachment_id}", status_code=204)
def remove_attachment(
    attachment_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    delete_attachment(
        db=db,
        attachment_id=attachment_id,
        current_user=current_user,
        request=request,
    )
    db.commit()

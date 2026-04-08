from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import Attachment, User
from app.repositories.experiment_repo import get_experiment
from app.services.audit_service import log_action
from app.storage.local import storage

# Allowed upload MIME types and extensions
ALLOWED_EXTENSIONS = {
    ".pdf", ".xlsx", ".xls", ".docx", ".doc", ".csv", ".txt",
    ".fcs", ".lif", ".czi", ".png", ".jpg", ".jpeg", ".zip",
}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/csv",
    "text/plain",
    "image/png",
    "image/jpeg",
    "application/zip",
    "application/octet-stream",  # .fcs, .lif, .czi
}


def _validate_file(file: UploadFile, data: bytes) -> None:
    import os

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{ext}' is not allowed. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    ct = (file.content_type or "").lower().split(";")[0].strip()
    if ct and ct not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Content type '{ct}' is not allowed",
        )


async def save_attachment(
    db: Session,
    exp_id: uuid.UUID,
    file: UploadFile,
    description: Optional[str],
    current_user: User,
    request: Optional[Request] = None,
) -> Attachment:
    import os

    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    data = await file.read()
    _validate_file(file, data)

    ext = os.path.splitext(file.filename or "")[1].lower()
    stored_name = f"{uuid.uuid4()}{ext}"
    relative_path = f"{exp.experiment_id}/{stored_name}"

    storage.save(relative_path, data)

    attachment = Attachment(
        experiment_id=exp_id,
        filename=file.filename or stored_name,
        stored_filename=stored_name,
        file_path=relative_path,
        content_type=file.content_type or "application/octet-stream",
        file_size_bytes=len(data),
        uploaded_by=current_user.id,
        description=description,
    )
    db.add(attachment)
    db.flush()

    log_action(
        db=db,
        entity_type="attachment",
        entity_id=str(attachment.id),
        action="uploaded",
        actor=current_user,
        new_value={
            "experiment_id": str(exp_id),
            "filename": attachment.filename,
            "size_bytes": len(data),
        },
        request=request,
    )
    return attachment


def delete_attachment(
    db: Session,
    attachment_id: uuid.UUID,
    current_user: User,
    request: Optional[Request] = None,
) -> None:
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found"
        )

    log_action(
        db=db,
        entity_type="attachment",
        entity_id=str(attachment.id),
        action="deleted",
        actor=current_user,
        old_value={
            "experiment_id": str(attachment.experiment_id),
            "filename": attachment.filename,
            "file_path": attachment.file_path,
        },
        request=request,
    )

    # Remove from storage
    try:
        storage.delete(attachment.file_path)
    except Exception:
        pass  # Log but don't fail if physical file already gone

    db.delete(attachment)
    db.flush()

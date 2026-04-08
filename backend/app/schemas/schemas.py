"""
Pydantic v2 request/response schemas for the Electronic Lab Notebook API.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Shared config
# ---------------------------------------------------------------------------


class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Auth / Token
# ---------------------------------------------------------------------------


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------------------
# User / Role
# ---------------------------------------------------------------------------


class UserRoleOut(_Base):
    id: uuid.UUID
    role: str
    assigned_at: datetime
    assigned_by: Optional[uuid.UUID] = None


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)
    roles: List[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserOut(_Base):
    id: uuid.UUID
    username: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserWithRoles(UserOut):
    roles: List[UserRoleOut] = []


class RoleAssign(BaseModel):
    role: str


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


class ProjectCreate(BaseModel):
    project_code: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = "active"


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectOut(_Base):
    id: uuid.UUID
    project_code: str
    title: str
    description: Optional[str] = None
    status: str
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Experiment
# ---------------------------------------------------------------------------


class ExperimentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    purpose: str = Field(..., min_length=1)
    project_id: uuid.UUID
    barcode: Optional[str] = None


class ExperimentUpdate(BaseModel):
    title: Optional[str] = None
    purpose: Optional[str] = None
    barcode: Optional[str] = None


class StatusTransition(BaseModel):
    new_status: str
    comment: Optional[str] = None


class ParticipantAdd(BaseModel):
    user_id: uuid.UUID
    role: str


class ExperimentParticipantOut(_Base):
    id: uuid.UUID
    user_id: uuid.UUID
    role: str
    added_at: datetime
    user: Optional[UserOut] = None


class ExperimentOut(_Base):
    id: uuid.UUID
    experiment_id: str
    title: str
    purpose: str
    project_id: uuid.UUID
    owner_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    barcode: Optional[str] = None
    version: int


class ExperimentDetail(ExperimentOut):
    participants: List[ExperimentParticipantOut] = []
    entries: List["LabEntryOut"] = []
    materials: List["ExperimentMaterialOut"] = []


# ---------------------------------------------------------------------------
# Lab Entries
# ---------------------------------------------------------------------------


class LabEntryUpdate(BaseModel):
    content: str


class LabEntryOut(_Base):
    id: uuid.UUID
    experiment_id: uuid.UUID
    section: str
    content: str
    version: int
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------


class MaterialCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    catalog_number: Optional[str] = None
    vendor: Optional[str] = None
    barcode: Optional[str] = None
    inventory_id: Optional[str] = None


class MaterialOut(_Base):
    id: uuid.UUID
    name: str
    catalog_number: Optional[str] = None
    vendor: Optional[str] = None
    barcode: Optional[str] = None
    inventory_id: Optional[str] = None
    created_at: datetime


class ExperimentMaterialCreate(BaseModel):
    material_id: Optional[uuid.UUID] = None
    material_name: str = Field(..., min_length=1, max_length=255)
    lot_number: Optional[str] = None
    quantity_used: Optional[float] = None
    unit: Optional[str] = None
    barcode: Optional[str] = None
    inventory_id: Optional[str] = None
    notes: Optional[str] = None


class ExperimentMaterialOut(_Base):
    id: uuid.UUID
    experiment_id: uuid.UUID
    material_id: Optional[uuid.UUID] = None
    material_name: str
    lot_number: Optional[str] = None
    quantity_used: Optional[float] = None
    unit: Optional[str] = None
    barcode: Optional[str] = None
    inventory_id: Optional[str] = None
    notes: Optional[str] = None
    added_by: uuid.UUID
    added_at: datetime


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------


class AttachmentOut(_Base):
    id: uuid.UUID
    experiment_id: uuid.UUID
    filename: str
    stored_filename: str
    content_type: str
    file_size_bytes: int
    uploaded_by: uuid.UUID
    uploaded_at: datetime
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1)
    comment_type: str = "general"


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1)


class CommentOut(_Base):
    id: uuid.UUID
    experiment_id: uuid.UUID
    author_id: uuid.UUID
    comment_type: str
    content: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------


class ReviewCreate(BaseModel):
    reviewer_id: uuid.UUID


class ReviewUpdate(BaseModel):
    status: str  # approved / returned / in_review
    comments: Optional[str] = None


class ReviewOut(_Base):
    id: uuid.UUID
    experiment_id: uuid.UUID
    reviewer_id: uuid.UUID
    status: str
    comments: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Signatures
# ---------------------------------------------------------------------------


class SignatureCreate(BaseModel):
    signature_type: str  # completion / review / approval
    meaning: str = Field(
        ...,
        min_length=10,
        description="The legal meaning of this signature, e.g. 'I confirm the above experiment was conducted as described'",
    )


class SignatureOut(_Base):
    id: uuid.UUID
    experiment_id: uuid.UUID
    signer_id: uuid.UUID
    signature_type: str
    meaning: str
    signed_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------


class AuditLogOut(_Base):
    id: uuid.UUID
    entity_type: str
    entity_id: str
    action: str
    actor_id: Optional[uuid.UUID] = None
    actor_username: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    timestamp: datetime


class PaginatedAuditLog(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[AuditLogOut]

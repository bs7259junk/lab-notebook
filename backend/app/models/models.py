"""
SQLAlchemy 2.x ORM models for the Electronic Lab Notebook.

IMPORTANT: The AuditLog table must NEVER have rows updated or deleted.
It is an append-only immutable audit trail required for 21 CFR Part 11 compliance.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


# ---------------------------------------------------------------------------
# Role constants
# ---------------------------------------------------------------------------

VALID_ROLES = {"admin", "scientist", "technician", "research_associate", "reviewer"}


# ---------------------------------------------------------------------------
# User & Roles
# ---------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        foreign_keys="UserRole.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_email", "email"),
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    assigned_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="roles"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "role", name="uq_user_role"),
        Index("ix_user_roles_user_id", "user_id"),
    )


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    experiments: Mapped[list["Experiment"]] = relationship(
        "Experiment", back_populates="project"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("ix_projects_created_by", "created_by"),
        Index("ix_projects_project_code", "project_code"),
    )


# ---------------------------------------------------------------------------
# Experiment
# ---------------------------------------------------------------------------


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )  # e.g. EXP-2026-001
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    barcode: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="experiments")
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])
    participants: Mapped[list["ExperimentParticipant"]] = relationship(
        "ExperimentParticipant", back_populates="experiment", cascade="all, delete-orphan"
    )
    entries: Mapped[list["LabEntry"]] = relationship(
        "LabEntry", back_populates="experiment", cascade="all, delete-orphan"
    )
    materials: Mapped[list["ExperimentMaterial"]] = relationship(
        "ExperimentMaterial", back_populates="experiment", cascade="all, delete-orphan"
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment", back_populates="experiment", cascade="all, delete-orphan"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="experiment", cascade="all, delete-orphan"
    )
    signatures: Mapped[list["Signature"]] = relationship(
        "Signature", back_populates="experiment", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="experiment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_experiments_experiment_id", "experiment_id"),
        Index("ix_experiments_project_id", "project_id"),
        Index("ix_experiments_owner_id", "owner_id"),
        Index("ix_experiments_status", "status"),
        Index("ix_experiments_barcode", "barcode"),
    )


class ExperimentParticipant(Base):
    __tablename__ = "experiment_participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    experiment: Mapped["Experiment"] = relationship(
        "Experiment", back_populates="participants"
    )
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("experiment_id", "user_id", name="uq_experiment_participant"),
        Index("ix_experiment_participants_experiment_id", "experiment_id"),
        Index("ix_experiment_participants_user_id", "user_id"),
    )


# ---------------------------------------------------------------------------
# Lab Entries
# ---------------------------------------------------------------------------

LAB_ENTRY_SECTIONS = {
    "purpose",
    "materials_notes",
    "method_protocol",
    "raw_data",
    "observations",
}


class LabEntry(Base):
    __tablename__ = "lab_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    section: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="entries")
    author: Mapped["User"] = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        UniqueConstraint("experiment_id", "section", name="uq_lab_entry_section"),
        Index("ix_lab_entries_experiment_id", "experiment_id"),
    )


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    catalog_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vendor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    inventory_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # hook for future inventory system
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_materials_barcode", "barcode"),)


class ExperimentMaterial(Base):
    __tablename__ = "experiment_materials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    # null = manual entry not linked to material catalog
    material_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id", ondelete="SET NULL"), nullable=True
    )
    material_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # denormalized for manual entry
    lot_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quantity_used: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    inventory_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    added_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    experiment: Mapped["Experiment"] = relationship(
        "Experiment", back_populates="materials"
    )
    material: Mapped[Optional["Material"]] = relationship("Material")
    added_by_user: Mapped["User"] = relationship("User", foreign_keys=[added_by])

    __table_args__ = (
        Index("ix_experiment_materials_experiment_id", "experiment_id"),
        Index("ix_experiment_materials_material_id", "material_id"),
        Index("ix_experiment_materials_barcode", "barcode"),
    )


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)  # original name
    stored_filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # uuid-based stored name
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    experiment: Mapped["Experiment"] = relationship(
        "Experiment", back_populates="attachments"
    )
    uploader: Mapped["User"] = relationship("User", foreign_keys=[uploaded_by])

    __table_args__ = (Index("ix_attachments_experiment_id", "experiment_id"),)


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    comment_type: Mapped[str] = mapped_column(
        String(20), default="general", nullable=False
    )  # general / review
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    experiment: Mapped["Experiment"] = relationship(
        "Experiment", back_populates="comments"
    )
    author: Mapped["User"] = relationship("User", foreign_keys=[author_id])

    __table_args__ = (
        Index("ix_comments_experiment_id", "experiment_id"),
        Index("ix_comments_author_id", "author_id"),
    )


# ---------------------------------------------------------------------------
# Signatures (e-signatures)
# ---------------------------------------------------------------------------


class Signature(Base):
    __tablename__ = "signatures"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    signer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    signature_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # completion / review / approval
    meaning: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # e.g. "I confirm the above experiment was conducted as described"
    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    experiment: Mapped["Experiment"] = relationship(
        "Experiment", back_populates="signatures"
    )
    signer: Mapped["User"] = relationship("User", foreign_keys=[signer_id])

    __table_args__ = (
        Index("ix_signatures_experiment_id", "experiment_id"),
        Index("ix_signatures_signer_id", "signer_id"),
    )


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    # CONSTRAINT: reviewer_id != experiment.owner_id — enforced in service layer
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending / in_review / approved / returned
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    experiment: Mapped["Experiment"] = relationship(
        "Experiment", back_populates="reviews"
    )
    reviewer: Mapped["User"] = relationship("User", foreign_keys=[reviewer_id])

    __table_args__ = (
        Index("ix_reviews_experiment_id", "experiment_id"),
        Index("ix_reviews_reviewer_id", "reviewer_id"),
    )


# ---------------------------------------------------------------------------
# AuditLog — IMMUTABLE. NEVER UPDATE OR DELETE ROWS.
# ---------------------------------------------------------------------------


class AuditLog(Base):
    """
    IMMUTABLE AUDIT TRAIL — 21 CFR Part 11 compliance requirement.

    DO NOT add update or delete operations on this table anywhere in the codebase.
    Rows are append-only. Modifying or removing audit records is a compliance violation.
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # experiment/user/project/attachment/comment/signature/review
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # created/updated/status_changed/signed/reviewed/uploaded/deleted/login/logout
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # null for system actions
    actor_username: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # denormalized — preserved even if user deleted
    old_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )  # server-side timestamp — NEVER from client

    actor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[actor_id])

    __table_args__ = (
        Index("ix_audit_logs_entity_type_entity_id", "entity_type", "entity_id"),
        Index("ix_audit_logs_actor_id", "actor_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_timestamp", "timestamp"),
    )

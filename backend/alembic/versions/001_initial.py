"""Initial schema — all tables

Revision ID: 001
Revises:
Create Date: 2026-04-05

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    # ------------------------------------------------------------------
    # user_roles
    # ------------------------------------------------------------------
    op.create_table(
        "user_roles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "assigned_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.UniqueConstraint("user_id", "role", name="uq_user_role"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])

    # ------------------------------------------------------------------
    # projects
    # ------------------------------------------------------------------
    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_code", sa.String(50), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column(
            "created_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_projects_created_by", "projects", ["created_by"])
    op.create_index("ix_projects_project_code", "projects", ["project_code"])

    # ------------------------------------------------------------------
    # experiments
    # ------------------------------------------------------------------
    op.create_table(
        "experiments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("experiment_id", sa.String(50), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "owner_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("barcode", sa.String(100), nullable=True, unique=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_experiments_experiment_id", "experiments", ["experiment_id"])
    op.create_index("ix_experiments_project_id", "experiments", ["project_id"])
    op.create_index("ix_experiments_owner_id", "experiments", ["owner_id"])
    op.create_index("ix_experiments_status", "experiments", ["status"])
    op.create_index("ix_experiments_barcode", "experiments", ["barcode"])

    # ------------------------------------------------------------------
    # experiment_participants
    # ------------------------------------------------------------------
    op.create_table(
        "experiment_participants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "experiment_id",
            UUID(as_uuid=True),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "experiment_id", "user_id", name="uq_experiment_participant"
        ),
    )
    op.create_index(
        "ix_experiment_participants_experiment_id",
        "experiment_participants",
        ["experiment_id"],
    )
    op.create_index(
        "ix_experiment_participants_user_id",
        "experiment_participants",
        ["user_id"],
    )

    # ------------------------------------------------------------------
    # lab_entries
    # ------------------------------------------------------------------
    op.create_table(
        "lab_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "experiment_id",
            UUID(as_uuid=True),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("experiment_id", "section", name="uq_lab_entry_section"),
    )
    op.create_index("ix_lab_entries_experiment_id", "lab_entries", ["experiment_id"])

    # ------------------------------------------------------------------
    # materials
    # ------------------------------------------------------------------
    op.create_table(
        "materials",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("catalog_number", sa.String(100), nullable=True),
        sa.Column("vendor", sa.String(255), nullable=True),
        sa.Column("barcode", sa.String(100), nullable=True),
        sa.Column("inventory_id", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_materials_barcode", "materials", ["barcode"])

    # ------------------------------------------------------------------
    # experiment_materials
    # ------------------------------------------------------------------
    op.create_table(
        "experiment_materials",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "experiment_id",
            UUID(as_uuid=True),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "material_id",
            UUID(as_uuid=True),
            sa.ForeignKey("materials.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("material_name", sa.String(255), nullable=False),
        sa.Column("lot_number", sa.String(100), nullable=True),
        sa.Column("quantity_used", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("barcode", sa.String(100), nullable=True),
        sa.Column("inventory_id", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "added_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_experiment_materials_experiment_id",
        "experiment_materials",
        ["experiment_id"],
    )
    op.create_index(
        "ix_experiment_materials_material_id",
        "experiment_materials",
        ["material_id"],
    )
    op.create_index(
        "ix_experiment_materials_barcode", "experiment_materials", ["barcode"]
    )

    # ------------------------------------------------------------------
    # attachments
    # ------------------------------------------------------------------
    op.create_table(
        "attachments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "experiment_id",
            UUID(as_uuid=True),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column(
            "uploaded_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("ix_attachments_experiment_id", "attachments", ["experiment_id"])

    # ------------------------------------------------------------------
    # comments
    # ------------------------------------------------------------------
    op.create_table(
        "comments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "experiment_id",
            UUID(as_uuid=True),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "comment_type", sa.String(20), nullable=False, server_default="general"
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.create_index("ix_comments_experiment_id", "comments", ["experiment_id"])
    op.create_index("ix_comments_author_id", "comments", ["author_id"])

    # ------------------------------------------------------------------
    # signatures
    # ------------------------------------------------------------------
    op.create_table(
        "signatures",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "experiment_id",
            UUID(as_uuid=True),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "signer_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("signature_type", sa.String(20), nullable=False),
        sa.Column("meaning", sa.Text(), nullable=False),
        sa.Column(
            "signed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
    )
    op.create_index("ix_signatures_experiment_id", "signatures", ["experiment_id"])
    op.create_index("ix_signatures_signer_id", "signatures", ["signer_id"])

    # ------------------------------------------------------------------
    # reviews
    # ------------------------------------------------------------------
    op.create_table(
        "reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "experiment_id",
            UUID(as_uuid=True),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_reviews_experiment_id", "reviews", ["experiment_id"])
    op.create_index("ix_reviews_reviewer_id", "reviews", ["reviewer_id"])

    # ------------------------------------------------------------------
    # audit_logs  (IMMUTABLE — NEVER UPDATE OR DELETE ROWS)
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column(
            "actor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_username", sa.String(100), nullable=True),
        sa.Column("old_value", sa.JSON(), nullable=True),
        sa.Column("new_value", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_audit_logs_entity_type_entity_id",
        "audit_logs",
        ["entity_type", "entity_id"],
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("reviews")
    op.drop_table("signatures")
    op.drop_table("comments")
    op.drop_table("attachments")
    op.drop_table("experiment_materials")
    op.drop_table("materials")
    op.drop_table("lab_entries")
    op.drop_table("experiment_participants")
    op.drop_table("experiments")
    op.drop_table("projects")
    op.drop_table("user_roles")
    op.drop_table("users")

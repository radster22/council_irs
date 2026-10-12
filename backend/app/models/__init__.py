from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CHAR,
    Date,
    DECIMAL,
    Enum,
    FetchedValue,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    JSON,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = (UniqueConstraint("ein", name="uq_org_ein"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    ein: Mapped[str] = mapped_column(String(10), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    org_type: Mapped[str] = mapped_column(Enum("CBO", "CITY_AGENCY", name="organization_type"), nullable=False, server_default=text("'CBO'"))
    borough: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(Enum("ACTIVE", "INACTIVE", name="organization_status"), nullable=False, server_default=text("'ACTIVE'"))
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=FetchedValue(),
    )

    user_links: Mapped[list["UserOrganization"]] = relationship(back_populates="organization")
    initiative_links: Mapped[list["InitiativeOrganization"]] = relationship(back_populates="organization")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="email"),
        Index("idx_user_role", "role"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("COUNCIL_ADMIN", "COUNCIL_REVIEWER", "EXTERNAL_SUBMITTER", "VIEW_ONLY", name="user_role"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP"))

    organization_links: Mapped[list["UserOrganization"]] = relationship(back_populates="user")
    created_submissions: Mapped[list["Submission"]] = relationship(
        back_populates="creator",
        foreign_keys="Submission.created_by",
    )
    uploaded_attachments: Mapped[list["Attachment"]] = relationship(back_populates="uploader")
    submitted_versions: Mapped[list["SubmissionVersion"]] = relationship(back_populates="submitter")


class UserOrganization(Base):
    __tablename__ = "user_organizations"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", name="fk_uo_user", ondelete="RESTRICT", onupdate="NO ACTION"), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", name="fk_uo_org", ondelete="RESTRICT", onupdate="NO ACTION"),
        primary_key=True,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP"))

    user: Mapped[User] = relationship(back_populates="organization_links")
    organization: Mapped[Organization] = relationship(back_populates="user_links")


class Initiative(Base):
    __tablename__ = "initiatives"
    __table_args__ = (
        UniqueConstraint("code", name="code"),
        Index("idx_init_fy", "fiscal_year"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("ACTIVE", "COMBINED", "RETIRED", name="initiative_status"),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=FetchedValue(),
    )

    organization_links: Mapped[list["InitiativeOrganization"]] = relationship(back_populates="initiative")
    predecessor_links: Mapped[list["InitiativeRelationship"]] = relationship(
        back_populates="successor",
        foreign_keys="InitiativeRelationship.successor_id",
    )
    successor_links: Mapped[list["InitiativeRelationship"]] = relationship(
        back_populates="predecessor",
        foreign_keys="InitiativeRelationship.predecessor_id",
    )
    reporting_cycles: Mapped[list["ReportingCycle"]] = relationship(back_populates="initiative")
    form_templates: Mapped[list["FormTemplate"]] = relationship(back_populates="initiative")


class InitiativeOrganization(Base):
    __tablename__ = "initiative_organizations"

    initiative_id: Mapped[str] = mapped_column(ForeignKey("initiatives.id", name="fk_io_initiative", ondelete="RESTRICT", onupdate="NO ACTION"), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", name="fk_io_organization", ondelete="RESTRICT", onupdate="NO ACTION"),
        primary_key=True,
    )
    awarded_amount: Mapped[Decimal] = mapped_column(DECIMAL(14, 2), nullable=False, server_default=text("0.00"))
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP"))

    initiative: Mapped[Initiative] = relationship(back_populates="organization_links")
    organization: Mapped[Organization] = relationship(back_populates="initiative_links")


class InitiativeRelationship(Base):
    __tablename__ = "initiative_relationships"

    predecessor_id: Mapped[str] = mapped_column(ForeignKey("initiatives.id", name="fk_rel_pred", ondelete="RESTRICT", onupdate="NO ACTION"), primary_key=True)
    successor_id: Mapped[str] = mapped_column(ForeignKey("initiatives.id", name="fk_rel_succ", ondelete="RESTRICT", onupdate="NO ACTION"), primary_key=True)
    relationship_type: Mapped[str] = mapped_column(Enum("RENAMED", "COMBINED", name="initiative_relationship_type"), primary_key=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP"))

    predecessor: Mapped[Initiative] = relationship(back_populates="successor_links", foreign_keys=[predecessor_id])
    successor: Mapped[Initiative] = relationship(back_populates="predecessor_links", foreign_keys=[successor_id])


class ReportingCycle(Base):
    __tablename__ = "reporting_cycles"
    __table_args__ = (
        UniqueConstraint("initiative_id", "id", name="uq_cycle_init"),
        UniqueConstraint("initiative_id", "cycle_name", name="uq_cycle_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    initiative_id: Mapped[str] = mapped_column(ForeignKey("initiatives.id", name="fk_cycle_init", ondelete="RESTRICT", onupdate="NO ACTION"), nullable=False)
    cycle_name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("UPCOMING", "OPEN", "CLOSED", name="reporting_cycle_status"),
        nullable=False,
        server_default=text("'UPCOMING'"),
    )
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP"))

    initiative: Mapped[Initiative] = relationship(back_populates="reporting_cycles")


class FormTemplate(Base):
    __tablename__ = "form_templates"
    __table_args__ = (
        UniqueConstraint("initiative_id", "version", name="uq_form_template_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    initiative_id: Mapped[str] = mapped_column(ForeignKey("initiatives.id", name="fk_form_init", ondelete="RESTRICT", onupdate="NO ACTION"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    schema_definition: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP"))

    initiative: Mapped[Initiative] = relationship(back_populates="form_templates")


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["initiative_id", "cycle_id"],
            ["reporting_cycles.initiative_id", "reporting_cycles.id"],
            name="fk_sub_cycle_init",
            ondelete="RESTRICT",
            onupdate="NO ACTION",
        ),
        ForeignKeyConstraint(
            ["initiative_id", "template_version"],
            ["form_templates.initiative_id", "form_templates.version"],
            name="fk_sub_form_template",
            ondelete="RESTRICT",
            onupdate="NO ACTION",
        ),
        ForeignKeyConstraint(
            ["initiative_id", "organization_id"],
            ["initiative_organizations.initiative_id", "initiative_organizations.organization_id"],
            name="fk_sub_init_org",
            ondelete="RESTRICT",
            onupdate="NO ACTION",
        ),
        ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_sub_creator",
            ondelete="RESTRICT",
            onupdate="NO ACTION",
        ),
        UniqueConstraint("id", "template_version", name="uq_sub_id_template"),
        UniqueConstraint("initiative_id", "organization_id", "cycle_id", name="uq_sub_instance"),
        Index("idx_sub_triage", "is_balanced", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    initiative_id: Mapped[str] = mapped_column(String(36), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(36), nullable=False)
    cycle_id: Mapped[str] = mapped_column(String(36), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("DRAFT", "SUBMITTED", "IN_REVIEW", "REVISION_REQUESTED", "APPROVED", "REJECTED", name="submission_status"),
        nullable=False,
        server_default=text("'DRAFT'"),
    )
    form_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    allocated_budget: Mapped[Decimal] = mapped_column(DECIMAL(14, 2), nullable=False, server_default=text("0.00"))
    total_budget: Mapped[Decimal] = mapped_column(DECIMAL(14, 2), nullable=False, server_default=text("0.00"))
    is_balanced: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=FetchedValue(),
    )

    creator: Mapped[User] = relationship(back_populates="created_submissions", foreign_keys=[created_by])
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="submission")
    budget_line_items: Mapped[list["BudgetLineItem"]] = relationship(back_populates="submission")


class BudgetLineItem(Base):
    __tablename__ = "budget_line_items"
    __table_args__ = (UniqueConstraint("submission_id", "line_number", name="uq_line_item"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id", name="fk_line_item_sub", ondelete="RESTRICT", onupdate="NO ACTION"), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    budgeted_amount: Mapped[Decimal] = mapped_column(DECIMAL(14, 2), nullable=False, server_default=text("0.00"))
    actual_amount: Mapped[Decimal | None] = mapped_column(DECIMAL(14, 2), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=FetchedValue(),
    )

    submission: Mapped[Submission] = relationship(back_populates="budget_line_items")


class SubmissionVersion(Base):
    __tablename__ = "submission_versions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["submission_id", "template_version"],
            ["submissions.id", "submissions.template_version"],
            name="fk_ver_sub_template",
            ondelete="RESTRICT",
            onupdate="NO ACTION",
        ),
        ForeignKeyConstraint(
            ["submitted_by"],
            ["users.id"],
            name="fk_ver_user",
            ondelete="RESTRICT",
            onupdate="NO ACTION",
        ),
        UniqueConstraint("submission_id", "version_number", name="uq_sub_ver"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    submission_id: Mapped[str] = mapped_column(String(36), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    form_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    budget_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    submitted_by: Mapped[str] = mapped_column(String(36), nullable=False)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP"))

    submitter: Mapped[User] = relationship(back_populates="submitted_versions")


class Attachment(Base):
    __tablename__ = "attachments"
    __table_args__ = (
        ForeignKeyConstraint(["submission_id"], ["submissions.id"], name="fk_att_sub", ondelete="RESTRICT", onupdate="NO ACTION"),
        ForeignKeyConstraint(["uploaded_by"], ["users.id"], name="fk_att_user", ondelete="RESTRICT", onupdate="NO ACTION"),
        UniqueConstraint("bucket_name", "object_key", name="uq_attachment_location"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    submission_id: Mapped[str] = mapped_column(String(36), nullable=False)
    bucket_name: Mapped[str] = mapped_column(String(100), nullable=False)
    object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(150), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(CHAR(64), nullable=True)
    uploaded_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP"))

    submission: Mapped[Submission] = relationship(back_populates="attachments")
    uploader: Mapped[User] = relationship(back_populates="uploaded_attachments")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_sub", "submission_id"),
        Index("idx_audit_time", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id", name="fk_audit_sub", ondelete="RESTRICT", onupdate="NO ACTION"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(50), nullable=False)
    state_diff: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP"))



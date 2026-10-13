from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    email: str


class AuthenticatedUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    organization_ids: list[str] = Field(default_factory=list)


class AdminUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    organization_ids: list[str] = Field(default_factory=list)


class AdminUserCreateRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=12, max_length=72)
    role: Literal["COUNCIL_ADMIN", "COUNCIL_REVIEWER", "EXTERNAL_SUBMITTER", "VIEW_ONLY"]
    organization_eins: list[str] = Field(default_factory=list)


class OrganizationCreateRequest(BaseModel):
    ein: str = Field(..., pattern=r"^\d{2}-?\d{7}$")
    legal_name: str = Field(..., min_length=1, max_length=255)
    org_type: Literal["CBO", "CITY_AGENCY"]
    borough: str | None = Field(default=None, max_length=50)


class BudgetLineInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    category: str = ""
    description: str | None = Field(default=None, max_length=500)
    amount: str | Decimal = ""
    actual_amount: str | Decimal | None = None


class BudgetValidationRequest(BaseModel):
    lines: list[BudgetLineInput]


class BudgetValidationResponse(BaseModel):
    line_count: int
    total: str
    is_valid: bool
    errors: list[str]


class SaveSubmissionRequest(BaseModel):
    status: Literal["DRAFT", "SUBMITTED"] = "DRAFT"
    form_data: dict[str, Any] = Field(default_factory=dict)
    budget_lines: list[BudgetLineInput] = Field(default_factory=list)


class CreateSubmissionRequest(BaseModel):
    initiative_id: str = Field(..., min_length=1, max_length=36)
    cycle_id: str = Field(..., min_length=1, max_length=36)
    organization_id: str | None = Field(default=None, min_length=1, max_length=36)


class AvailableReportResponse(BaseModel):
    initiative_id: str
    initiative_name: str
    organization_id: str
    organization_name: str
    cycle_id: str
    cycle_name: str
    template_version: int


class SubmissionListItemResponse(BaseModel):
    submission_id: str
    initiative_name: str
    organization_name: str
    cycle_name: str
    status: str
    total_budget: str


class CreateSubmissionResponse(BaseModel):
    submission_id: str
    initiative_id: str
    organization_id: str
    cycle_id: str
    template_version: int
    status: str


class AttachmentSummaryResponse(BaseModel):
    attachment_id: str
    submission_id: str
    original_filename: str
    content_type: str
    file_size_bytes: int
    checksum_sha256: str


class SubmissionDetailResponse(CreateSubmissionResponse):
    form_data: dict[str, Any] = Field(default_factory=dict)
    budget_lines: list[BudgetLineInput] = Field(default_factory=list)
    form_schema: dict[str, Any] = Field(default_factory=dict)
    attachments: list[AttachmentSummaryResponse] = Field(default_factory=list)
    initiative_name: str = ""
    organization_name: str = ""
    cycle_name: str = ""
    allocated_budget: str = "0.00"
    total_budget: str = "0.00"
    is_balanced: bool = False
    audit_history: list[dict[str, Any]] = Field(default_factory=list)
    versions: list[dict[str, Any]] = Field(default_factory=list)


class ReviewQueueItemResponse(BaseModel):
    submission_id: str
    initiative_name: str
    organization_name: str
    cycle_name: str
    status: str
    total_budget: str
    is_balanced: bool
    updated_at: str | None = None
    is_incomplete: bool = False
    validation_errors: list[str] = Field(default_factory=list)
    organization_ein: str = ""
    borough: str | None = None
    fiscal_year: int
    initiative_id: str
    cycle_id: str


class ReviewActionRequest(BaseModel):
    action: Literal["START_REVIEW", "REQUEST_REVISION", "APPROVE", "REJECT"]
    comment: str | None = Field(default=None, max_length=5000)


class ReviewActionResponse(BaseModel):
    submission_id: str
    status: str
    action: str


class SaveSubmissionResponse(BaseModel):
    submission_id: str
    status: str
    form_data: dict[str, Any] = Field(default_factory=dict)
    total_budget: str
    is_balanced: bool
    line_count: int
    is_valid: bool
    validation_errors: list[str] = Field(default_factory=list)
    saved_by: str


class AttachmentUploadResponse(AttachmentSummaryResponse):
    uploaded_by: str


class AdminEditSubmissionRequest(BaseModel):
    form_data: dict[str, Any] = Field(default_factory=dict)
    budget_lines: list[BudgetLineInput] = Field(default_factory=list)
    comment: str = Field(..., min_length=1, max_length=5000)


class AdminUserUpdateRequest(BaseModel):
    role: Literal["COUNCIL_ADMIN", "COUNCIL_REVIEWER", "EXTERNAL_SUBMITTER", "VIEW_ONLY"]
    is_active: bool
    organization_eins: list[str] | None = None


class AdminPasswordResetRequest(BaseModel):
    password: str = Field(..., min_length=12, max_length=72)


class InitiativeCreateRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    fiscal_year: int = Field(..., ge=2000, le=2200)


class InitiativeUpdateRequest(BaseModel):
    status: Literal["ACTIVE", "COMBINED", "RETIRED"]
    name: str | None = Field(default=None, min_length=1, max_length=255)


class CycleCreateRequest(BaseModel):
    cycle_name: str = Field(..., min_length=1, max_length=100)
    start_date: date
    due_date: date
    status: Literal["UPCOMING", "OPEN", "CLOSED"] = "UPCOMING"


class CycleUpdateRequest(BaseModel):
    status: Literal["UPCOMING", "OPEN", "CLOSED"]


class AssignmentCreateRequest(BaseModel):
    ein: str = Field(..., min_length=9, max_length=10)
    awarded_amount: Decimal = Field(..., ge=0, max_digits=14, decimal_places=2)


class FormTemplateCreateRequest(BaseModel):
    schema_definition: dict[str, Any]
    is_published: bool = False


class RolloverRequest(BaseModel):
    source_fiscal_year: int = Field(..., ge=2000, le=2200)
    destination_fiscal_year: int = Field(..., ge=2001, le=2201)


class RolloverResponse(BaseModel):
    initiatives_created: int
    cycles_created: int
    templates_created: int
    assignments_created: int



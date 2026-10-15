from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db import get_db
from app.models import Attachment, AuditLog, BudgetLineItem, FormTemplate, Initiative, Organization, ReportingCycle, SubmissionVersion, User
from app.schemas import (
    AttachmentSummaryResponse,
    AttachmentUploadResponse,
    AvailableReportResponse,
    CreateSubmissionRequest,
    CreateSubmissionResponse,
    SaveSubmissionRequest,
    SaveSubmissionResponse,
    SubmissionListItemResponse,
    SubmissionDetailResponse,
    ReviewActionRequest,
    ReviewActionResponse,
    ReviewQueueItemResponse,
    AdminEditSubmissionRequest,
)
from app.services.submission_service import (
    SubmissionError,
    create_draft_submission,
    apply_review_action,
    edit_submitted_submission,
    get_form_fields,
    get_submission_for_user,
    list_review_queue,
    list_available_reports,
    list_user_submissions,
    persist_submission,
)
from app.services.upload_service import UPLOAD_ROOT, sanitize_submission_id, save_uploaded_file

router = APIRouter(prefix="/api/submissions", tags=["submissions"])
logger = logging.getLogger(__name__)


def _raise_submission_error(exc: SubmissionError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/available", response_model=list[AvailableReportResponse])
def available_reports(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AvailableReportResponse]:
    return [AvailableReportResponse(**item) for item in list_available_reports(db, user)]


@router.get("", response_model=list[SubmissionListItemResponse])
def user_submissions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SubmissionListItemResponse]:
    return [SubmissionListItemResponse(**item) for item in list_user_submissions(db, user)]


@router.get("/review-queue", response_model=list[ReviewQueueItemResponse])
def review_queue(
    status_filter: str | None = Query(default=None, alias="status"),
    query: str | None = Query(default=None, max_length=255),
    balanced: bool | None = Query(default=None),
    ein: str | None = Query(default=None, max_length=10),
    borough: str | None = Query(default=None, max_length=50),
    fiscal_year: int | None = Query(default=None, ge=2000, le=2200),
    initiative: str | None = Query(default=None, max_length=255),
    cycle: str | None = Query(default=None, max_length=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ReviewQueueItemResponse]:
    statuses = {"DRAFT", "SUBMITTED", "IN_REVIEW", "REVISION_REQUESTED", "APPROVED", "REJECTED"}
    if status_filter and status_filter not in statuses:
        raise HTTPException(status_code=400, detail="Unsupported review status filter.")
    try:
        items = list_review_queue(db, user, status_filter=status_filter, query=query, balanced=balanced,
                                  ein=ein, borough=borough, fiscal_year=fiscal_year,
                                  initiative=initiative, cycle=cycle)
    except SubmissionError as exc:
        _raise_submission_error(exc)
    return [ReviewQueueItemResponse(**item) for item in items]


@router.post("", response_model=CreateSubmissionResponse, status_code=status.HTTP_201_CREATED)
def start_submission(
    payload: CreateSubmissionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreateSubmissionResponse:
    try:
        submission = create_draft_submission(
            db,
            user,
            payload.initiative_id,
            payload.cycle_id,
            payload.organization_id,
        )
    except SubmissionError as exc:
        _raise_submission_error(exc)
    return CreateSubmissionResponse(
        submission_id=submission.id,
        initiative_id=submission.initiative_id,
        organization_id=submission.organization_id,
        cycle_id=submission.cycle_id,
        template_version=submission.template_version,
        status=submission.status,
    )


@router.get("/{submission_id}", response_model=SubmissionDetailResponse)
def get_submission(
    submission_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubmissionDetailResponse:
    try:
        submission = get_submission_for_user(db, user, sanitize_submission_id(submission_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SubmissionError as exc:
        _raise_submission_error(exc)

    items = db.scalars(
        select(BudgetLineItem)
        .where(BudgetLineItem.submission_id == submission.id)
        .order_by(BudgetLineItem.line_number)
    ).all()
    attachments = db.scalars(
        select(Attachment)
        .where(Attachment.submission_id == submission.id)
        .order_by(Attachment.created_at)
    ).all()
    template = db.scalar(
        select(FormTemplate).where(
            FormTemplate.initiative_id == submission.initiative_id,
            FormTemplate.version == submission.template_version,
        )
    )
    form_data = dict(submission.form_data or {})
    saved_draft_lines = form_data.pop("_draft_budget_lines", None)
    budget_lines = saved_draft_lines if submission.status == "DRAFT" and isinstance(saved_draft_lines, list) else [
        {"category": item.category, "description": item.description, "amount": str(item.budgeted_amount),
         "actual_amount": str(item.actual_amount) if item.actual_amount is not None else None} for item in items
    ]
    return SubmissionDetailResponse(
        submission_id=submission.id,
        initiative_id=submission.initiative_id,
        organization_id=submission.organization_id,
        cycle_id=submission.cycle_id,
        template_version=submission.template_version,
        status=submission.status,
        form_data=form_data,
        budget_lines=budget_lines,
        form_schema={
            **template.schema_definition,
            "fields": get_form_fields(template.schema_definition),
        } if template is not None else {"fields": []},
        attachments=[
            AttachmentSummaryResponse(
                attachment_id=item.id,
                submission_id=item.submission_id,
                original_filename=item.original_filename,
                content_type=item.content_type,
                file_size_bytes=item.file_size_bytes,
                checksum_sha256=item.checksum_sha256 or "",
            )
            for item in attachments
        ],
        initiative_name=db.get(Initiative, submission.initiative_id).name,
        organization_name=db.get(Organization, submission.organization_id).legal_name,
        cycle_name=db.get(ReportingCycle, submission.cycle_id).cycle_name,
        allocated_budget=str(submission.allocated_budget),
        total_budget=str(submission.total_budget),
        is_balanced=submission.is_balanced,
        audit_history=[
            {
                "action": event.action,
                "actor_role": event.actor_role,
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "state_diff": event.state_diff or {},
            }
            for event in db.scalars(
                select(AuditLog)
                .where(AuditLog.submission_id == submission.id)
                .order_by(AuditLog.created_at, AuditLog.id)
            ).all()
        ],
        versions=[
            {"version_number": version.version_number, "template_version": version.template_version,
             "submitted_at": version.submitted_at.isoformat() if version.submitted_at else None,
             "reviewer_notes": version.reviewer_notes,
             "form_snapshot": version.form_snapshot,
             "budget_snapshot": version.budget_snapshot}
            for version in db.scalars(select(SubmissionVersion)
                .where(SubmissionVersion.submission_id == submission.id)
                .order_by(SubmissionVersion.version_number.desc())).all()
        ],
    )


@router.post("/{submission_id}/review", response_model=ReviewActionResponse)
def review_submission(
    submission_id: str,
    payload: ReviewActionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReviewActionResponse:
    try:
        submission = get_submission_for_user(db, user, sanitize_submission_id(submission_id))
        next_status = apply_review_action(db, submission, user, payload.action, payload.comment)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SubmissionError as exc:
        _raise_submission_error(exc)
    return ReviewActionResponse(submission_id=submission.id, status=next_status, action=payload.action)


@router.post("/{submission_id}/admin-edit", response_model=ReviewActionResponse)
def admin_edit_submission(
    submission_id: str,
    payload: AdminEditSubmissionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReviewActionResponse:
    try:
        submission = get_submission_for_user(db, user, sanitize_submission_id(submission_id))
        edit_submitted_submission(db, submission, user, payload.form_data,
                                  [line.model_dump() for line in payload.budget_lines], payload.comment)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SubmissionError as exc:
        _raise_submission_error(exc)
    return ReviewActionResponse(submission_id=submission.id, status=submission.status, action="ADMIN_EDIT")


@router.get("/{submission_id}/attachments/{attachment_id}")
def download_submission_attachment(
    submission_id: str,
    attachment_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    try:
        submission = get_submission_for_user(db, user, sanitize_submission_id(submission_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SubmissionError as exc:
        _raise_submission_error(exc)
    attachment = db.scalar(select(Attachment).where(
        Attachment.id == attachment_id,
        Attachment.submission_id == submission.id,
    ))
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found.")
    root = UPLOAD_ROOT.resolve()
    stored_path = (root / attachment.object_key).resolve()
    if not stored_path.is_relative_to(root) or not stored_path.is_file():
        raise HTTPException(status_code=404, detail="Attachment file is unavailable.")
    return FileResponse(
        path=stored_path,
        media_type=attachment.content_type,
        filename=attachment.original_filename,
    )


@router.post("/{submission_id}/save", response_model=SaveSubmissionResponse)
def save_submission(
    submission_id: str,
    payload: SaveSubmissionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SaveSubmissionResponse:
    try:
        submission = get_submission_for_user(
            db,
            user,
            sanitize_submission_id(submission_id),
            write=True,
        )
        summary = persist_submission(
            db,
            submission,
            user,
            payload.status,
            payload.form_data,
            [line.model_dump() for line in payload.budget_lines],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SubmissionError as exc:
        _raise_submission_error(exc)

    if payload.status == "SUBMITTED":
        logger.info("submission confirmation prepared submission_id=%s actor_id=%s total_budget=%s line_count=%s",
                    submission.id, user.id, summary["total"], summary["line_count"])

    return SaveSubmissionResponse(
        submission_id=submission.id,
        status=submission.status,
        form_data=payload.form_data,
        total_budget=summary["total"],
        is_balanced=submission.is_balanced,
        line_count=summary["line_count"],
        is_valid=bool(summary["is_valid"]),
        validation_errors=list(summary.get("errors", [])),
        saved_by=user.email,
    )


@router.post("/{submission_id}/attachments", response_model=AttachmentUploadResponse)
async def upload_submission_attachment(
    submission_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttachmentUploadResponse:
    saved: dict[str, object] | None = None
    try:
        safe_submission_id = sanitize_submission_id(submission_id)
        submission = get_submission_for_user(db, user, safe_submission_id, write=True)
        saved = await save_uploaded_file(safe_submission_id, file)
        attachment = Attachment(
            id=str(uuid4()),
            submission_id=submission.id,
            bucket_name="local",
            object_key=str(saved["stored_path"]),
            original_filename=str(saved["original_filename"]),
            content_type=str(saved["content_type"]),
            file_size_bytes=int(saved["file_size_bytes"]),
            checksum_sha256=str(saved["checksum_sha256"]),
            uploaded_by=user.id,
        )
        db.add(attachment)
        db.commit()
    except ValueError as exc:
        message = str(exc)
        if "25 MB" in message:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc
    except SubmissionError as exc:
        _raise_submission_error(exc)
    except Exception:
        db.rollback()
        if saved is not None:
            stored_path = (UPLOAD_ROOT / str(saved["stored_path"])).resolve()
            if stored_path.is_relative_to(UPLOAD_ROOT.resolve()) and stored_path.is_file():
                stored_path.unlink()
        raise

    assert saved is not None
    return AttachmentUploadResponse(
        attachment_id=attachment.id,
        submission_id=str(saved["submission_id"]),
        original_filename=str(saved["original_filename"]),
        content_type=str(saved["content_type"]),
        file_size_bytes=int(saved["file_size_bytes"]),
        checksum_sha256=str(saved["checksum_sha256"]),
        uploaded_by=user.email,
    )

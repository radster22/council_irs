from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_organization_ids
from app.models import (
    AuditLog,
    BudgetLineItem,
    FormTemplate,
    Initiative,
    InitiativeOrganization,
    Organization,
    ReportingCycle,
    Submission,
    SubmissionVersion,
    User,
    UserOrganization,
)
from app.services.budget_service import validate_budget_lines


class SubmissionError(Exception):
    def __init__(self, detail: str, status_code: int) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def list_available_reports(db: Session, user: User) -> list[dict[str, object]]:
    if user.role != "EXTERNAL_SUBMITTER":
        return []
    organization_ids = get_accessible_organization_ids(db, user.id)
    if not organization_ids:
        return []

    latest_templates = (
        select(FormTemplate.initiative_id, func.max(FormTemplate.version).label("template_version"))
        .where(FormTemplate.is_published.is_(True))
        .group_by(FormTemplate.initiative_id)
        .subquery()
    )
    rows = db.execute(
        select(
            Initiative.id,
            Initiative.name,
            Organization.id,
            Organization.legal_name,
            ReportingCycle.id,
            ReportingCycle.cycle_name,
            latest_templates.c.template_version,
        )
        .join(InitiativeOrganization, InitiativeOrganization.initiative_id == Initiative.id)
        .join(Organization, Organization.id == InitiativeOrganization.organization_id)
        .join(
            ReportingCycle,
            ReportingCycle.initiative_id == Initiative.id,
        )
        .join(latest_templates, latest_templates.c.initiative_id == Initiative.id)
        .where(
            Initiative.status == "ACTIVE",
            Organization.status == "ACTIVE",
            ReportingCycle.status == "OPEN",
            InitiativeOrganization.organization_id.in_(organization_ids),
        )
        .order_by(Initiative.name, Organization.legal_name, ReportingCycle.start_date)
    ).all()

    existing = set(
        db.execute(
            select(Submission.initiative_id, Submission.organization_id, Submission.cycle_id).where(
                Submission.organization_id.in_(organization_ids)
            )
        ).all()
    )
    return [
        {
            "initiative_id": row[0],
            "initiative_name": row[1],
            "organization_id": row[2],
            "organization_name": row[3],
            "cycle_id": row[4],
            "cycle_name": row[5],
            "template_version": row[6],
        }
        for row in rows
        if (row[0], row[2], row[4]) not in existing
    ]


def list_user_submissions(db: Session, user: User) -> list[dict[str, object]]:
    statement = (
        select(
            Submission.id,
            Initiative.name,
            Organization.legal_name,
            ReportingCycle.cycle_name,
            Submission.status,
            Submission.total_budget,
        )
        .join(Initiative, Initiative.id == Submission.initiative_id)
        .join(Organization, Organization.id == Submission.organization_id)
        .join(ReportingCycle, ReportingCycle.id == Submission.cycle_id)
        .order_by(Submission.updated_at.desc(), Submission.created_at.desc())
    )
    if user.role not in {"COUNCIL_ADMIN", "COUNCIL_REVIEWER"}:
        organization_ids = get_accessible_organization_ids(db, user.id)
        if not organization_ids:
            return []
        statement = statement.where(Submission.organization_id.in_(organization_ids))

    return [
        {
            "submission_id": row[0],
            "initiative_name": row[1],
            "organization_name": row[2],
            "cycle_name": row[3],
            "status": row[4],
            "total_budget": str(row[5]),
        }
        for row in db.execute(statement).all()
    ]


def list_review_queue(
    db: Session,
    user: User,
    *,
    status_filter: str | None = None,
    query: str | None = None,
    balanced: bool | None = None,
) -> list[dict[str, object]]:
    if user.role not in {"COUNCIL_ADMIN", "COUNCIL_REVIEWER", "VIEW_ONLY"}:
        raise SubmissionError("Council access is required.", 403)
    statement = (
        select(
            Submission.id,
            Initiative.name,
            Organization.legal_name,
            ReportingCycle.cycle_name,
            Submission.status,
            Submission.total_budget,
            Submission.is_balanced,
            Submission.updated_at,
        )
        .join(Initiative, Initiative.id == Submission.initiative_id)
        .join(Organization, Organization.id == Submission.organization_id)
        .join(ReportingCycle, ReportingCycle.id == Submission.cycle_id)
        .where(Submission.status != "DRAFT")
        .order_by(Submission.updated_at.desc(), Submission.created_at.desc())
    )
    if status_filter:
        statement = statement.where(Submission.status == status_filter)
    if query:
        pattern = f"%{query.strip()}%"
        statement = statement.where(or_(
            Submission.id.like(pattern),
            Initiative.name.like(pattern),
            Organization.legal_name.like(pattern),
            ReportingCycle.cycle_name.like(pattern),
        ))
    if balanced is not None:
        statement = statement.where(Submission.is_balanced.is_(balanced))
    return [
        {
            "submission_id": row[0],
            "initiative_name": row[1],
            "organization_name": row[2],
            "cycle_name": row[3],
            "status": row[4],
            "total_budget": str(row[5]),
            "is_balanced": bool(row[6]),
            "updated_at": row[7].isoformat() if row[7] else None,
        }
        for row in db.execute(statement).all()
    ]


def apply_review_action(
    db: Session,
    submission: Submission,
    user: User,
    action: str,
    comment: str | None,
) -> str:
    if user.role not in {"COUNCIL_ADMIN", "COUNCIL_REVIEWER"}:
        raise SubmissionError("Only Council reviewers and administrators can update review status.", 403)
    transitions = {
        ("SUBMITTED", "START_REVIEW"): "IN_REVIEW",
        ("IN_REVIEW", "REQUEST_REVISION"): "REVISION_REQUESTED",
        ("IN_REVIEW", "APPROVE"): "APPROVED",
        ("IN_REVIEW", "REJECT"): "REJECTED",
    }
    next_status = transitions.get((submission.status, action))
    if next_status is None:
        raise SubmissionError(f"Action {action} is not valid while submission is {submission.status}.", 409)
    previous_status = submission.status
    submission.status = next_status
    values: dict[str, object] = {
        "submission_id": submission.id,
        "action": action,
        "actor_id": user.id,
        "actor_role": user.role,
        "state_diff": {
            "from": previous_status,
            "to": next_status,
            "comment": comment.strip() if comment else None,
        },
    }
    if db.bind is not None and db.bind.dialect.name == "sqlite":
        values["id"] = (db.scalar(select(func.max(AuditLog.id))) or 0) + 1
    db.add(submission)
    db.add(AuditLog(**values))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return next_status


def create_draft_submission(
    db: Session,
    user: User,
    initiative_id: str,
    cycle_id: str,
    organization_id: str | None,
) -> Submission:
    if user.role != "EXTERNAL_SUBMITTER":
        raise SubmissionError("Only external submitters can start a report.", 403)

    accessible = get_accessible_organization_ids(db, user.id)
    if organization_id is None:
        if len(accessible) != 1:
            raise SubmissionError("Choose an organization associated with your account.", 422)
        organization_id = accessible[0]
    elif organization_id not in accessible:
        raise SubmissionError("Organization access denied.", 403)

    assignment = db.get(InitiativeOrganization, (initiative_id, organization_id))
    organization = db.get(Organization, organization_id)
    cycle = db.get(ReportingCycle, cycle_id)
    initiative = db.get(Initiative, initiative_id)
    if (
        assignment is None
        or cycle is None
        or initiative is None
        or organization is None
        or organization.status != "ACTIVE"
        or cycle.initiative_id != initiative_id
        or cycle.status != "OPEN"
        or initiative.status != "ACTIVE"
    ):
        raise SubmissionError("No open report is available for this assignment.", 404)

    template = db.scalar(
        select(FormTemplate)
        .where(FormTemplate.initiative_id == initiative_id, FormTemplate.is_published.is_(True))
        .order_by(FormTemplate.version.desc())
        .limit(1)
    )
    if template is None:
        raise SubmissionError("No published report form is available for this initiative.", 409)

    existing = db.scalar(
        select(Submission).where(
            Submission.initiative_id == initiative_id,
            Submission.organization_id == organization_id,
            Submission.cycle_id == cycle_id,
        )
    )
    if existing is not None:
        raise SubmissionError("A report already exists for this assignment and cycle.", 409)

    submission = Submission(
        id=str(uuid4()),
        initiative_id=initiative_id,
        organization_id=organization_id,
        cycle_id=cycle_id,
        template_version=template.version,
        status="DRAFT",
        form_data={},
        allocated_budget=assignment.awarded_amount,
        total_budget=Decimal("0.00"),
        is_balanced=False,
        created_by=user.id,
    )
    db.add(submission)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise SubmissionError("A report already exists for this assignment and cycle.", 409) from exc
    db.refresh(submission)
    return submission


def get_submission_for_user(db: Session, user: User, submission_id: str, *, write: bool = False) -> Submission:
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise SubmissionError("Submission not found.", 404)

    if user.role not in {"COUNCIL_ADMIN", "COUNCIL_REVIEWER", "VIEW_ONLY"}:
        membership = db.get(UserOrganization, (user.id, submission.organization_id))
        if membership is None:
            raise SubmissionError("Submission access denied.", 403)

    if write:
        if user.role not in {"EXTERNAL_SUBMITTER", "COUNCIL_ADMIN"}:
            raise SubmissionError("This account cannot edit submissions.", 403)
        if submission.status not in {"DRAFT", "REVISION_REQUESTED"}:
            raise SubmissionError("This submission is not open for editing.", 409)

    return submission


def persist_submission(
    db: Session,
    submission: Submission,
    user: User,
    status: str,
    form_data: dict[str, object],
    budget_lines: list[dict[str, object]],
) -> dict[str, object]:
    is_submitting = status == "SUBMITTED"
    summary = validate_budget_lines(
        budget_lines,
        require_positive=is_submitting,
        require_category=is_submitting,
    )
    if not summary["is_valid"]:
        raise SubmissionError(
            "; ".join(str(error) for error in summary["errors"]),
            400,
        )

    template = db.scalar(
        select(FormTemplate).where(
            FormTemplate.initiative_id == submission.initiative_id,
            FormTemplate.version == submission.template_version,
        )
    )
    if is_submitting:
        if template is None or not template.is_published:
            raise SubmissionError("The report form is unavailable for submission.", 409)
        validate_form_data(template.schema_definition, form_data)

        actual_total = Decimal(str(summary["total"]))
        expected_total = _get_configured_budget_total(template.schema_definition, submission, form_data)
        if expected_total is not None and actual_total != expected_total:
            raise SubmissionError(
                f"Budget total must equal the configured amount ({expected_total:.2f}).",
                400,
            )

    db.execute(delete(BudgetLineItem).where(BudgetLineItem.submission_id == submission.id))
    snapshot_lines: list[dict[str, object]] = []
    for index, line in enumerate(budget_lines, start=1):
        category = str(line.get("category", "")).strip()
        amount = Decimal(str(line.get("amount", "0")))
        snapshot_lines.append({"line_number": index, "category": category, "amount": str(amount)})
        db.add(
            BudgetLineItem(
                id=str(uuid4()),
                submission_id=submission.id,
                line_number=index,
                category=category,
                budgeted_amount=amount,
            )
        )

    was_revision = submission.status == "REVISION_REQUESTED"
    submission.form_data = form_data
    submission.total_budget = Decimal(str(summary["total"]))
    expected_total = _get_configured_budget_total(template.schema_definition, submission, form_data) if template else None
    submission.is_balanced = expected_total is None or submission.total_budget == expected_total
    submission.status = "SUBMITTED" if is_submitting else ("REVISION_REQUESTED" if was_revision else "DRAFT")

    if is_submitting:
        next_version = (db.scalar(
            select(func.max(SubmissionVersion.version_number)).where(
                SubmissionVersion.submission_id == submission.id
            )
        ) or 0) + 1
        db.add(
            SubmissionVersion(
                id=str(uuid4()),
                submission_id=submission.id,
                version_number=next_version,
                template_version=submission.template_version,
                form_snapshot=form_data,
                budget_snapshot={"lines": snapshot_lines, "total": str(summary["total"])},
                submitted_by=user.id,
            )
        )
        audit_values: dict[str, object] = {
            "submission_id": submission.id,
            "action": "SUBMITTED",
            "actor_id": user.id,
            "actor_role": user.role,
            "state_diff": {"from": "REVISION_REQUESTED" if was_revision else "DRAFT", "to": "SUBMITTED"},
        }
        if db.bind is not None and db.bind.dialect.name == "sqlite":
            audit_values["id"] = (db.scalar(select(func.max(AuditLog.id))) or 0) + 1
        db.add(AuditLog(**audit_values))

    db.add(submission)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return summary


def validate_form_data(schema: dict[str, object], form_data: dict[str, object]) -> None:
    if not isinstance(schema, dict):
        raise SubmissionError("The published form definition is invalid.", 409)
    fields = get_form_fields(schema)

    errors: list[str] = []
    supported_types = {"text", "textarea", "narrative", "integer", "number", "currency", "percentage", "date", "select", "dropdown", "boolean"}
    for field in fields:
        if not isinstance(field, dict) or not isinstance(field.get("id"), str):
            errors.append("The published form contains an invalid field definition.")
            continue
        field_id = str(field["id"])
        label = str(field.get("label") or field_id)
        value = form_data.get(field_id)
        if value is None or value == "" or value == []:
            if field.get("required"):
                errors.append(f"Required field is missing: {label}.")
            continue
        if isinstance(value, str) and not value.strip() and field.get("required"):
            errors.append(f"Required field is missing: {label}.")
            continue

        field_type = str(field.get("type", "text"))
        if field_type not in supported_types:
            errors.append(f"The published form uses an unsupported field type for {label}.")
            continue
        try:
            if field_type in {"text", "textarea", "narrative"} and not isinstance(value, str):
                errors.append(f"{label} must be text.")
            elif field_type in {"text", "textarea", "narrative"} and "max_length" in field and len(str(value)) > int(field["max_length"]):
                errors.append(f"{label} exceeds the maximum length.")
            elif field_type in {"text", "textarea", "narrative"} and "max_words" in field and len(str(value).split()) > int(field["max_words"]):
                errors.append(f"{label} exceeds the maximum word count.")
            elif field_type == "integer":
                parsed = int(str(value))
                if "minimum" in field and parsed < int(field["minimum"]):
                    errors.append(f"{label} is below the minimum value.")
                if "maximum" in field and parsed > int(field["maximum"]):
                    errors.append(f"{label} exceeds the maximum value.")
            elif field_type in {"number", "currency", "percentage"}:
                if field_type == "currency" and not isinstance(value, str):
                    errors.append(f"{label} must be submitted as a decimal string.")
                    continue
                parsed_decimal = Decimal(str(value))
                if not parsed_decimal.is_finite():
                    errors.append(f"{label} must be a finite number.")
                if field_type == "currency" and parsed_decimal.is_finite() and parsed_decimal.quantize(Decimal("0.01")) != parsed_decimal:
                    errors.append(f"{label} can have at most two decimal places.")
                if "minimum" in field and parsed_decimal < Decimal(str(field["minimum"])):
                    errors.append(f"{label} is below the minimum value.")
                if "maximum" in field and parsed_decimal > Decimal(str(field["maximum"])):
                    errors.append(f"{label} exceeds the maximum value.")
            elif field_type == "date":
                date.fromisoformat(str(value))
            elif field_type in {"select", "dropdown"}:
                options = field.get("options")
                if not isinstance(options, list) or value not in options:
                    errors.append(f"{label} must be one of the configured options.")
            elif field_type == "boolean" and not isinstance(value, bool):
                errors.append(f"{label} must be true or false.")
        except (ValueError, TypeError, InvalidOperation):
            errors.append(f"{label} has an invalid {field_type} value.")

    if errors:
        raise SubmissionError(" ".join(errors), 400)


def get_form_fields(schema: dict[str, object]) -> list[object]:
    fields = schema.get("fields", [])
    sections = schema.get("sections", [])
    if not isinstance(fields, list) or not isinstance(sections, list):
        raise SubmissionError("The published form has an invalid fields definition.", 409)
    combined = list(fields)
    for section in sections:
        if not isinstance(section, dict):
            raise SubmissionError("The published form contains an invalid section definition.", 409)
        section_fields = section.get("fields", [])
        if not isinstance(section_fields, list):
            raise SubmissionError("The published form section has an invalid fields definition.", 409)
        combined.extend(section_fields)
    return combined


def _get_configured_budget_total(
    schema: dict[str, object],
    submission: Submission,
    form_data: dict[str, object],
) -> Decimal | None:
    rule = schema.get("budget_reconciliation")
    if rule is None:
        return None
    if not isinstance(rule, dict):
        raise SubmissionError("The published budget reconciliation rule is invalid.", 409)

    target = rule.get("target")
    if target == "allocated_budget":
        return Decimal(str(submission.allocated_budget))
    if isinstance(target, dict) and isinstance(target.get("field_id"), str):
        raw_value = form_data.get(str(target["field_id"]))
    elif isinstance(target, dict) and isinstance(target.get("amount"), str):
        raw_value = target["amount"]
    else:
        raise SubmissionError("The published budget reconciliation target is invalid.", 409)

    try:
        expected = Decimal(str(raw_value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise SubmissionError("The configured budget total is not numeric.", 400) from exc
    if not expected.is_finite() or expected < 0:
        raise SubmissionError("The configured budget total must be a finite, non-negative amount.", 400)
    try:
        if expected.quantize(Decimal("0.01")) != expected or expected > Decimal("999999999999.99"):
            raise SubmissionError("The configured budget total is outside the supported currency precision.", 400)
    except InvalidOperation as exc:
        raise SubmissionError("The configured budget total is outside the supported currency precision.", 400) from exc
    return expected

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db import get_db
from app.models import (
    Attachment,
    BudgetLineItem,
    FormTemplate,
    Initiative,
    InitiativeOrganization,
    InitiativeRelationship,
    Organization,
    ReportingCycle,
    Submission,
    User,
)
from app.schemas import (
    AssignmentCreateRequest,
    CycleCreateRequest,
    CycleUpdateRequest,
    FormTemplateCreateRequest,
    InitiativeCreateRequest,
    InitiativeUpdateRequest,
    OrganizationCreateRequest,
    RolloverRequest,
    RolloverResponse,
)
from app.services.organization_service import (
    find_organization_by_ein,
    import_organization_registry,
    normalize_ein,
    organization_details,
)

router = APIRouter(prefix="/api/admin", tags=["administration"])
COUNCIL_ROLES = ("COUNCIL_ADMIN", "COUNCIL_REVIEWER", "VIEW_ONLY")
MAX_REGISTRY_BYTES = 5 * 1024 * 1024


@router.get("/organizations")
def list_organizations(_: User = Depends(require_roles("COUNCIL_ADMIN")), db: Session = Depends(get_db)) -> list[dict[str, str]]:
    return [{"id": row.id, "ein": row.ein, "legal_name": row.legal_name}
            for row in db.scalars(select(Organization).where(Organization.status == "ACTIVE").order_by(Organization.legal_name)).all()]


@router.get("/organizations/lookup")
def lookup_organization(ein: str = Query(..., max_length=20), _: User = Depends(require_roles("COUNCIL_ADMIN")),
                        db: Session = Depends(get_db)) -> dict[str, str | None]:
    try:
        normalize_ein(ein)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    organization = find_organization_by_ein(db, ein)
    if organization is None:
        raise HTTPException(status_code=404, detail="No active organization in the registry has that EIN.")
    return organization_details(organization)


@router.post("/organizations/import")
async def import_organizations(file: UploadFile = File(...), _: User = Depends(require_roles("COUNCIL_ADMIN")),
                               db: Session = Depends(get_db)) -> dict[str, object]:
    content = await file.read(MAX_REGISTRY_BYTES + 1)
    if len(content) > MAX_REGISTRY_BYTES:
        raise HTTPException(status_code=413, detail="The registry file must be 5 MB or smaller.")
    try:
        return import_organization_registry(db, content)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="The registry could not be saved because of a conflicting EIN.") from exc


@router.post("/organizations", status_code=201)
def create_organization(payload: OrganizationCreateRequest, _: User = Depends(require_roles("COUNCIL_ADMIN")), db: Session = Depends(get_db)) -> dict[str, str | None]:
    ein_digits = payload.ein.replace("-", "")
    organization = Organization(
        id=str(uuid4()),
        ein=f"{ein_digits[:2]}-{ein_digits[2:]}",
        legal_name=payload.legal_name.strip(),
        org_type=payload.org_type,
        borough=payload.borough.strip() if payload.borough and payload.borough.strip() else None,
        status="ACTIVE",
    )
    if not organization.legal_name:
        raise HTTPException(status_code=422, detail="Organization legal name cannot be blank.")
    if find_organization_by_ein(db, payload.ein, active_only=False) is not None:
        raise HTTPException(status_code=409, detail="An organization with that EIN already exists.")
    db.add(organization)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An organization with that EIN already exists.") from exc
    return {"id": organization.id, "ein": organization.ein, "legal_name": organization.legal_name,
            "org_type": organization.org_type, "borough": organization.borough}


@router.get("/initiatives")
def list_initiatives(_: User = Depends(require_roles("COUNCIL_ADMIN")), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    initiatives = db.scalars(select(Initiative).order_by(Initiative.fiscal_year.desc(), Initiative.name)).all()
    result = []
    for item in initiatives:
        cycles = db.scalars(select(ReportingCycle).where(ReportingCycle.initiative_id == item.id).order_by(ReportingCycle.start_date)).all()
        assignments = db.execute(
            select(InitiativeOrganization, Organization)
            .join(Organization, Organization.id == InitiativeOrganization.organization_id)
            .where(InitiativeOrganization.initiative_id == item.id)
            .order_by(Organization.legal_name)
        ).all()
        templates = db.scalars(select(FormTemplate).where(FormTemplate.initiative_id == item.id).order_by(FormTemplate.version.desc())).all()
        result.append({
            "id": item.id, "code": item.code, "name": item.name,
            "fiscal_year": item.fiscal_year, "status": item.status,
            "cycles": [{"id": cycle.id, "cycle_name": cycle.cycle_name,
                        "start_date": cycle.start_date.isoformat(), "due_date": cycle.due_date.isoformat(),
                        "status": cycle.status} for cycle in cycles],
            "assignments": [{"organization_id": assignment.organization_id, "ein": organization.ein,
                             "legal_name": organization.legal_name, "awarded_amount": str(assignment.awarded_amount)}
                            for assignment, organization in assignments],
            "templates": [{"id": template.id, "version": template.version,
                           "is_published": template.is_published,
                           "schema_definition": template.schema_definition} for template in templates],
            "lineage": [{"relationship_type": relation.relationship_type,
                         "direction": "predecessor" if relation.successor_id == item.id else "successor",
                         "initiative_id": relation.predecessor_id if relation.successor_id == item.id else relation.successor_id,
                         "initiative_code": (db.get(Initiative, relation.predecessor_id if relation.successor_id == item.id else relation.successor_id)).code}
                        for relation in db.scalars(select(InitiativeRelationship).where(
                            (InitiativeRelationship.predecessor_id == item.id) |
                            (InitiativeRelationship.successor_id == item.id)
                        )).all()],
        })
    return result


@router.post("/initiatives", status_code=201)
def create_initiative(payload: InitiativeCreateRequest, _: User = Depends(require_roles("COUNCIL_ADMIN")), db: Session = Depends(get_db)) -> dict[str, str | int]:
    if not payload.code.strip() or not payload.name.strip():
        raise HTTPException(status_code=422, detail="Initiative code and name cannot be blank.")
    initiative = Initiative(id=str(uuid4()), code=payload.code.strip(), name=payload.name.strip(),
                            fiscal_year=payload.fiscal_year, status="ACTIVE")
    db.add(initiative)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Initiative code already exists or conflicts with the database.") from exc
    return {"id": initiative.id, "code": initiative.code, "name": initiative.name, "fiscal_year": initiative.fiscal_year}


@router.patch("/initiatives/{initiative_id}")
def update_initiative(initiative_id: str, payload: InitiativeUpdateRequest, _: User = Depends(require_roles("COUNCIL_ADMIN")), db: Session = Depends(get_db)) -> dict[str, str]:
    initiative = db.get(Initiative, initiative_id)
    if initiative is None:
        raise HTTPException(status_code=404, detail="Initiative not found.")
    if payload.name is not None:
        initiative.name = payload.name.strip()
    initiative.status = payload.status
    db.add(initiative)
    db.commit()
    return {"id": initiative.id, "name": initiative.name, "status": initiative.status}


@router.post("/initiatives/{initiative_id}/cycles", status_code=201)
def create_cycle(initiative_id: str, payload: CycleCreateRequest, _: User = Depends(require_roles("COUNCIL_ADMIN")), db: Session = Depends(get_db)) -> dict[str, object]:
    initiative = db.get(Initiative, initiative_id)
    if initiative is None:
        raise HTTPException(status_code=404, detail="Initiative not found.")
    if not payload.cycle_name.strip() or payload.start_date > payload.due_date:
        raise HTTPException(status_code=422, detail="Cycle start date must be on or before the due date.")
    cycle = ReportingCycle(id=str(uuid4()), initiative_id=initiative_id, cycle_name=payload.cycle_name.strip(),
                           start_date=payload.start_date, due_date=payload.due_date, status=payload.status)
    db.add(cycle)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A cycle with that name already exists for this initiative.") from exc
    return {"id": cycle.id, "cycle_name": cycle.cycle_name, "status": cycle.status}


@router.patch("/cycles/{cycle_id}")
def update_cycle(cycle_id: str, payload: CycleUpdateRequest, _: User = Depends(require_roles("COUNCIL_ADMIN")), db: Session = Depends(get_db)) -> dict[str, str]:
    cycle = db.get(ReportingCycle, cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Reporting cycle not found.")
    cycle.status = payload.status
    db.add(cycle)
    db.commit()
    return {"id": cycle.id, "status": cycle.status}


@router.post("/initiatives/{initiative_id}/assignments", status_code=201)
def create_assignment(initiative_id: str, payload: AssignmentCreateRequest, _: User = Depends(require_roles("COUNCIL_ADMIN")), db: Session = Depends(get_db)) -> dict[str, str]:
    if db.get(Initiative, initiative_id) is None:
        raise HTTPException(status_code=404, detail="Initiative not found.")
    organization = find_organization_by_ein(db, payload.ein)
    if organization is None:
        raise HTTPException(status_code=404, detail="No active organization has that EIN.")
    assignment = InitiativeOrganization(initiative_id=initiative_id, organization_id=organization.id,
                                       awarded_amount=payload.awarded_amount)
    db.add(assignment)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This organization is already assigned to the initiative.") from exc
    return {"initiative_id": initiative_id, "organization_id": organization.id,
            "awarded_amount": str(assignment.awarded_amount)}


@router.post("/initiatives/{initiative_id}/templates", status_code=201)
def create_template(initiative_id: str, payload: FormTemplateCreateRequest, _: User = Depends(require_roles("COUNCIL_ADMIN")), db: Session = Depends(get_db)) -> dict[str, object]:
    if db.get(Initiative, initiative_id) is None:
        raise HTTPException(status_code=404, detail="Initiative not found.")
    schema = payload.schema_definition
    top_fields = schema.get("fields", [])
    sections = schema.get("sections", [])
    if not isinstance(top_fields, list) or not isinstance(sections, list):
        raise HTTPException(status_code=422, detail="Form schema fields and sections must be lists.")
    fields = list(top_fields)
    for section in sections:
        if not isinstance(section, dict) or not isinstance(section.get("fields", []), list):
            raise HTTPException(status_code=422, detail="Every form section must contain a fields list.")
        fields.extend(section.get("fields", []))
    allowed_types = {"text", "textarea", "narrative", "integer", "number", "currency", "percentage", "date", "select", "dropdown", "boolean"}
    identifiers: set[str] = set()
    for field in fields:
        if not isinstance(field, dict) or not isinstance(field.get("id"), str) or not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,63}", field["id"]):
            raise HTTPException(status_code=422, detail="Every form field needs a valid identifier (letters, numbers, and underscores).")
        if field["id"] in identifiers:
            raise HTTPException(status_code=422, detail="Form field identifiers must be unique.")
        identifiers.add(field["id"])
        field_type = field.get("type", "text")
        if not isinstance(field_type, str) or field_type not in allowed_types:
            raise HTTPException(status_code=422, detail=f"Unsupported form field type for {field['id']}.")
        if field_type in {"select", "dropdown"} and (not isinstance(field.get("options"), list) or any(not isinstance(option, str) for option in field["options"])):
            raise HTTPException(status_code=422, detail=f"Select field {field['id']} needs an options list.")
    field_positions = {field["id"]: position for position, field in enumerate(fields) if isinstance(field, dict) and isinstance(field.get("id"), str)}
    for field in fields:
        if not isinstance(field, dict) or field.get("visible_when") is None:
            continue
        condition = field["visible_when"]
        source_field_id = condition.get("field_id") if isinstance(condition, dict) else None
        if (not isinstance(source_field_id, str) or source_field_id not in identifiers
                or field_positions[source_field_id] >= field_positions[field["id"]]
                or ("equals" in condition) == ("not_equals" in condition)
                or not set(condition).issubset({"field_id", "equals", "not_equals"})):
            raise HTTPException(status_code=422, detail=f"Conditional field {field['id']} needs one valid equals or not_equals rule referencing another field.")
    reconciliation = schema.get("budget_reconciliation")
    if reconciliation is not None:
        target = reconciliation.get("target") if isinstance(reconciliation, dict) else None
        valid_target = target == "allocated_budget"
        if isinstance(target, dict):
            field_id = target.get("field_id")
            amount = target.get("amount")
            valid_target = isinstance(field_id, str) and field_id in identifiers
            if isinstance(amount, str):
                try:
                    parsed_amount = Decimal(amount)
                    valid_target = parsed_amount.is_finite() and parsed_amount >= 0
                except Exception:
                    valid_target = False
        if not valid_target:
            raise HTTPException(status_code=422, detail="Budget reconciliation must target allocated_budget, a form field, or a non-negative fixed amount.")
    version = (db.scalar(select(func.max(FormTemplate.version)).where(FormTemplate.initiative_id == initiative_id)) or 0) + 1
    template = FormTemplate(id=str(uuid4()), initiative_id=initiative_id, version=version,
                            schema_definition=schema, is_published=payload.is_published)
    db.add(template)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A form version conflict occurred.") from exc
    return {"id": template.id, "version": template.version, "is_published": template.is_published}


@router.get("/obligations")
def list_open_obligations(_: User = Depends(require_roles(*COUNCIL_ROLES)), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    latest_templates = (
        select(FormTemplate.initiative_id, func.max(FormTemplate.version).label("version"))
        .where(FormTemplate.is_published.is_(True)).group_by(FormTemplate.initiative_id).subquery()
    )
    rows = db.execute(
        select(Initiative.id, Initiative.name, Organization.id, Organization.legal_name,
               Organization.borough, ReportingCycle.id, ReportingCycle.cycle_name,
               ReportingCycle.due_date, InitiativeOrganization.awarded_amount)
        .join(InitiativeOrganization, InitiativeOrganization.initiative_id == Initiative.id)
        .join(Organization, Organization.id == InitiativeOrganization.organization_id)
        .join(ReportingCycle, ReportingCycle.initiative_id == Initiative.id)
        .join(latest_templates, latest_templates.c.initiative_id == Initiative.id)
        .where(Initiative.status == "ACTIVE", Organization.status == "ACTIVE", ReportingCycle.status == "OPEN")
        .where(~select(Submission.id).where(Submission.initiative_id == Initiative.id,
               Submission.organization_id == Organization.id, Submission.cycle_id == ReportingCycle.id).exists())
        .order_by(ReportingCycle.due_date, Initiative.name, Organization.legal_name)
    ).all()
    today = date.today()
    return [{"initiative_id": row[0], "initiative_name": row[1], "organization_id": row[2],
             "organization_name": row[3], "borough": row[4], "cycle_id": row[5],
             "cycle_name": row[6], "due_date": row[7].isoformat(), "awarded_amount": str(row[8]),
             "is_overdue": row[7] < today}
            for row in rows]


@router.get("/analytics")
def analytics(_: User = Depends(require_roles(*COUNCIL_ROLES)), db: Session = Depends(get_db)) -> dict[str, object]:
    status_rows = db.execute(select(Submission.status, func.count(Submission.id)).group_by(Submission.status)).all()
    budget_rows = db.execute(select(func.coalesce(func.sum(Submission.allocated_budget), 0),
                                    func.coalesce(func.sum(Submission.total_budget), 0),
                                    func.count(Submission.id), func.sum(Submission.is_balanced)).where(
                                        Submission.status != "DRAFT")).one()
    borough_rows = db.execute(
        select(Organization.borough, func.coalesce(func.sum(Submission.total_budget), 0))
        .join(Submission, Submission.organization_id == Organization.id)
        .where(Submission.status != "DRAFT").group_by(Organization.borough).order_by(Organization.borough)
    ).all()
    return {
        "status_counts": {str(status): int(count) for status, count in status_rows},
        "allocated_budget": str(Decimal(str(budget_rows[0]))),
        "reported_budget": str(Decimal(str(budget_rows[1]))),
        "submitted_count": int(budget_rows[2] or 0),
        "balanced_count": int(budget_rows[3] or 0),
        "borough_totals": [{"borough": borough or "Unspecified", "total": str(Decimal(str(total)))} for borough, total in borough_rows],
    }


def _csv_bytes(rows: list[dict[str, object]], headers: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        safe = {}
        for key, value in row.items():
            text = "" if value is None else str(value)
            safe[key] = f"'{text}" if text.startswith(("=", "+", "-", "@")) else text
        writer.writerow(safe)
    return stream.getvalue().encode("utf-8-sig")


def _export_rows(db: Session) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    submission_rows = db.execute(select(Submission, Initiative.name, Organization.legal_name, ReportingCycle.cycle_name)
        .join(Initiative, Initiative.id == Submission.initiative_id)
        .join(Organization, Organization.id == Submission.organization_id)
        .join(ReportingCycle, ReportingCycle.id == Submission.cycle_id)
        .order_by(Submission.created_at)).all()
    submissions = [{"submission_id": sub.id, "initiative": init_name, "organization": org_name,
        "cycle": cycle_name, "status": sub.status, "allocated_budget": str(sub.allocated_budget),
        "total_budget": str(sub.total_budget), "is_balanced": sub.is_balanced,
        "form_data_json": json.dumps(sub.form_data or {}, ensure_ascii=False, separators=(",", ":")),
        "created_at": sub.created_at.isoformat() if sub.created_at else "",
        "updated_at": sub.updated_at.isoformat() if sub.updated_at else ""} for sub, init_name, org_name, cycle_name in submission_rows]
    budget_items = db.scalars(select(BudgetLineItem).order_by(BudgetLineItem.submission_id, BudgetLineItem.line_number)).all()
    budgets = [{"submission_id": line.submission_id, "line_number": line.line_number,
        "category": line.category, "description": line.description,
        "budgeted_amount": str(line.budgeted_amount),
        "actual_amount": str(line.actual_amount) if line.actual_amount is not None else ""} for line in budget_items]
    attachments = db.scalars(select(Attachment).order_by(Attachment.submission_id, Attachment.created_at)).all()
    files = [{"submission_id": item.submission_id, "filename": item.original_filename,
        "content_type": item.content_type, "file_size_bytes": item.file_size_bytes,
        "checksum_sha256": item.checksum_sha256 or "", "created_at": item.created_at.isoformat() if item.created_at else ""}
        for item in attachments]
    return submissions, budgets, files


def _spreadsheet_safe(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [{key: (f"'{value}" if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value)
             for key, value in row.items()} for row in rows]


@router.get("/exports/csv")
def export_csv(_: User = Depends(require_roles(*COUNCIL_ROLES)), db: Session = Depends(get_db)) -> StreamingResponse:
    submissions, budgets, files = _export_rows(db)
    bundle = io.BytesIO()
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("submissions.csv", _csv_bytes(submissions, ["submission_id", "initiative", "organization", "cycle", "status", "allocated_budget", "total_budget", "is_balanced", "form_data_json", "created_at", "updated_at"]))
        archive.writestr("budget_line_items.csv", _csv_bytes(budgets, ["submission_id", "line_number", "category", "description", "budgeted_amount", "actual_amount"]))
        archive.writestr("attachments.csv", _csv_bytes(files, ["submission_id", "filename", "content_type", "file_size_bytes", "checksum_sha256", "created_at"]))
    bundle.seek(0)
    return StreamingResponse(bundle, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=council-reporting-csv.zip"})


@router.get("/exports/xlsx")
def export_xlsx(_: User = Depends(require_roles(*COUNCIL_ROLES)), db: Session = Depends(get_db)) -> StreamingResponse:
    try:
        import pandas as pd
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="XLSX export dependencies are unavailable; install project requirements.") from exc
    submissions, budgets, files = _export_rows(db)
    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine="openpyxl") as writer:
        pd.DataFrame(_spreadsheet_safe(submissions)).to_excel(writer, sheet_name="Submissions", index=False)
        pd.DataFrame(_spreadsheet_safe(budgets)).to_excel(writer, sheet_name="Budget Lines", index=False)
        pd.DataFrame(_spreadsheet_safe(files)).to_excel(writer, sheet_name="Attachments", index=False)
    stream.seek(0)
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=council-reporting.xlsx"})


def _shift_year(value: date, years: int) -> date:
    target_year = value.year + years
    try:
        return value.replace(year=target_year)
    except ValueError:
        return value.replace(year=target_year, day=28)


@router.post("/rollover", response_model=RolloverResponse)
def rollover(payload: RolloverRequest, _: User = Depends(require_roles("COUNCIL_ADMIN")), db: Session = Depends(get_db)) -> RolloverResponse:
    if payload.destination_fiscal_year <= payload.source_fiscal_year:
        raise HTTPException(status_code=422, detail="Destination fiscal year must be later than source year.")
    sources = db.scalars(select(Initiative).where(Initiative.fiscal_year == payload.source_fiscal_year,
                                                   Initiative.status == "ACTIVE").order_by(Initiative.id)).all()
    if not sources:
        raise HTTPException(status_code=404, detail="No active initiatives exist for the source fiscal year.")
    initiatives_created = cycles_created = templates_created = assignments_created = 0
    try:
        for source in sources:
            suffix = f"-FY{payload.destination_fiscal_year}"
            base_code = source.code[:50-len(suffix)]
            target = Initiative(id=str(uuid4()), code=f"{base_code}{suffix}", name=source.name,
                                fiscal_year=payload.destination_fiscal_year, status="ACTIVE")
            db.add(target)
            db.flush()
            initiatives_created += 1
            db.add(InitiativeRelationship(predecessor_id=source.id, successor_id=target.id, relationship_type="RENAMED"))
            for assignment in db.scalars(select(InitiativeOrganization).where(InitiativeOrganization.initiative_id == source.id)).all():
                db.add(InitiativeOrganization(initiative_id=target.id, organization_id=assignment.organization_id,
                                              awarded_amount=assignment.awarded_amount))
                assignments_created += 1
            for cycle in db.scalars(select(ReportingCycle).where(ReportingCycle.initiative_id == source.id)).all():
                name = re.sub(str(payload.source_fiscal_year), str(payload.destination_fiscal_year), cycle.cycle_name)
                db.add(ReportingCycle(id=str(uuid4()), initiative_id=target.id, cycle_name=name,
                    start_date=_shift_year(cycle.start_date, payload.destination_fiscal_year - payload.source_fiscal_year),
                    due_date=_shift_year(cycle.due_date, payload.destination_fiscal_year - payload.source_fiscal_year),
                    status="UPCOMING"))
                cycles_created += 1
            for template in db.scalars(select(FormTemplate).where(FormTemplate.initiative_id == source.id)).all():
                db.add(FormTemplate(id=str(uuid4()), initiative_id=target.id, version=template.version,
                    schema_definition=template.schema_definition, is_published=template.is_published))
                templates_created += 1
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Rollover conflicts with an existing initiative, cycle, or lineage record.") from exc
    return RolloverResponse(initiatives_created=initiatives_created, cycles_created=cycles_created,
                            templates_created=templates_created, assignments_created=assignments_created)

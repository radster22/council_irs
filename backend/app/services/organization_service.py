from __future__ import annotations

import csv
import io
import re
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Organization

EIN_PATTERN = re.compile(r"^\d{2}-?\d{7}$")
ORG_TYPES = {"CBO", "CITY_AGENCY"}
ORG_STATUSES = {"ACTIVE", "INACTIVE"}
REGISTRY_COLUMNS = ("ein", "legal_name", "org_type", "borough", "status")
MAX_REGISTRY_ROWS = 10_000


def normalize_ein(raw: str) -> str:
    """Return the canonical XX-XXXXXXX form, or raise ValueError for a malformed EIN."""
    candidate = (raw or "").strip()
    if not EIN_PATTERN.match(candidate):
        raise ValueError("EIN must be 9 digits, formatted as 12-3456789.")
    digits = candidate.replace("-", "")
    return f"{digits[:2]}-{digits[2:]}"


def find_organization_by_ein(db: Session, raw: str, *, active_only: bool = True) -> Organization | None:
    """Look up the registry by EIN, accepting the hyphenated or digits-only form of a stored value."""
    candidate = (raw or "").strip()
    variants = {candidate, candidate.replace("-", "")}
    try:
        variants.add(normalize_ein(candidate))
    except ValueError:
        pass
    statement = select(Organization).where(Organization.ein.in_(variants))
    if active_only:
        statement = statement.where(Organization.status == "ACTIVE")
    return db.scalars(statement).first()


def organization_details(organization: Organization) -> dict[str, str | None]:
    return {
        "id": organization.id,
        "ein": organization.ein,
        "legal_name": organization.legal_name,
        "org_type": organization.org_type,
        "borough": organization.borough,
        "status": organization.status,
    }


def _parse_registry_rows(content: bytes) -> tuple[list[dict[str, str | None]], list[str]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return [], ["The registry file must be UTF-8 encoded CSV."]
    reader = csv.DictReader(io.StringIO(text))
    headers = {(name or "").strip().lower() for name in reader.fieldnames or []}
    missing = {"ein", "legal_name"} - headers
    if missing:
        return [], [f"Missing required column(s): {', '.join(sorted(missing))}."]

    rows: list[dict[str, str | None]] = []
    errors: list[str] = []
    seen: set[str] = set()
    for line_number, raw_row in enumerate(reader, start=2):
        if len(rows) + len(errors) >= MAX_REGISTRY_ROWS:
            errors.append(f"The registry file may contain at most {MAX_REGISTRY_ROWS} rows.")
            break
        row = {(key or "").strip().lower(): (value or "").strip() for key, value in raw_row.items() if key is not None}
        if not any(row.values()):
            continue
        try:
            ein = normalize_ein(row.get("ein", ""))
        except ValueError as exc:
            errors.append(f"Row {line_number}: {exc}")
            continue
        if ein in seen:
            errors.append(f"Row {line_number}: EIN {ein} appears more than once.")
            continue
        seen.add(ein)
        legal_name = row.get("legal_name", "")
        org_type = (row.get("org_type") or "CBO").upper()
        status = (row.get("status") or "ACTIVE").upper()
        borough = row.get("borough") or None
        if not legal_name or len(legal_name) > 255:
            errors.append(f"Row {line_number}: legal_name is required and must be at most 255 characters.")
        elif org_type not in ORG_TYPES:
            errors.append(f"Row {line_number}: org_type must be CBO or CITY_AGENCY.")
        elif status not in ORG_STATUSES:
            errors.append(f"Row {line_number}: status must be ACTIVE or INACTIVE.")
        elif borough is not None and len(borough) > 50:
            errors.append(f"Row {line_number}: borough must be at most 50 characters.")
        else:
            rows.append({"ein": ein, "legal_name": legal_name, "org_type": org_type, "borough": borough, "status": status})
    if not rows and not errors:
        errors.append("The registry file contains no organization rows.")
    return rows, errors


def import_organization_registry(db: Session, content: bytes) -> dict[str, object]:
    """Validate the authoritative Council Finance registry and reconcile it into `organizations`.

    The import is all-or-nothing: any invalid row rejects the file so the registry never holds a partial list.
    Organizations absent from the file are reported, never deleted or deactivated.
    """
    rows, errors = _parse_registry_rows(content)
    if errors:
        raise ValueError(" ".join(errors[:20]) + (f" ({len(errors) - 20} more errors.)" if len(errors) > 20 else ""))

    created = updated = unchanged = 0
    changes: list[str] = []
    for row in rows:
        existing = find_organization_by_ein(db, str(row["ein"]), active_only=False)
        if existing is None:
            db.add(Organization(id=str(uuid4()), **row))
            created += 1
            continue
        differences = [field for field in ("legal_name", "org_type", "borough", "status") if getattr(existing, field) != row[field]]
        if differences:
            for field in differences:
                setattr(existing, field, row[field])
            updated += 1
            changes.append(f"{existing.ein}: {', '.join(differences)}")
        else:
            unchanged += 1
    db.commit()

    listed_digits = {str(row["ein"]).replace("-", "") for row in rows}
    not_in_registry = [
        organization.ein
        for organization in db.scalars(select(Organization).where(Organization.status == "ACTIVE")).all()
        if organization.ein.replace("-", "") not in listed_digits
    ]
    return {
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "changes": changes,
        "active_not_in_registry": sorted(not_in_registry),
    }

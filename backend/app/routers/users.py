from __future__ import annotations

from collections import defaultdict
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.core.security import hash_password
from app.db import get_db
from app.models import Organization, User, UserOrganization
from app.schemas import AdminPasswordResetRequest, AdminUserCreateRequest, AdminUserResponse, AdminUserUpdateRequest

router = APIRouter(prefix="/api/admin/users", tags=["administration"])


@router.post("", response_model=AdminUserResponse, status_code=201)
def create_user(
    payload: AdminUserCreateRequest,
    _: User = Depends(require_roles("COUNCIL_ADMIN")),
    db: Session = Depends(get_db),
) -> AdminUserResponse:
    email = payload.email.strip().lower()
    full_name = payload.full_name.strip()
    if not email or not full_name:
        raise HTTPException(status_code=422, detail="Email and full name cannot be blank.")
    normalized_eins = list(dict.fromkeys(value.strip() for value in payload.organization_eins if value.strip()))
    if payload.role == "EXTERNAL_SUBMITTER" and not normalized_eins:
        raise HTTPException(status_code=422, detail="External submitters must have at least one organization assignment.")
    if payload.role != "EXTERNAL_SUBMITTER" and normalized_eins:
        raise HTTPException(status_code=422, detail="Only external submitters can be assigned organizations.")
    organizations = db.scalars(select(Organization).where(
        Organization.ein.in_(normalized_eins), Organization.status == "ACTIVE"
    )).all() if normalized_eins else []
    if len(organizations) != len(normalized_eins):
        raise HTTPException(status_code=422, detail="One or more EINs do not identify an active organization.")
    try:
        password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    user = User(id=str(uuid4()), email=email, password_hash=password_hash, full_name=full_name,
                role=payload.role, is_active=True)
    db.add(user)
    for index, organization in enumerate(organizations):
        db.add(UserOrganization(user_id=user.id, organization_id=organization.id, is_primary=index == 0))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with that email already exists.") from exc
    return AdminUserResponse(id=user.id, email=user.email, full_name=user.full_name, role=user.role,
                             is_active=user.is_active, organization_ids=[organization.id for organization in organizations])


@router.get("", response_model=list[AdminUserResponse])
def list_users(
    _: User = Depends(require_roles("COUNCIL_ADMIN")),
    db: Session = Depends(get_db),
) -> list[AdminUserResponse]:
    rows = db.execute(
        select(User, UserOrganization.organization_id)
        .outerjoin(UserOrganization, UserOrganization.user_id == User.id)
        .order_by(User.full_name, User.email)
    ).all()
    organizations: dict[str, list[str]] = defaultdict(list)
    users: dict[str, User] = {}
    for user, organization_id in rows:
        users[user.id] = user
        if organization_id is not None:
            organizations[user.id].append(organization_id)
    return [
        AdminUserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            organization_ids=organizations[user.id],
        )
        for user in users.values()
    ]


@router.patch("/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: str,
    payload: AdminUserUpdateRequest,
    actor: User = Depends(require_roles("COUNCIL_ADMIN")),
    db: Session = Depends(get_db),
) -> AdminUserResponse:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if actor.id == user.id and (not payload.is_active or payload.role != "COUNCIL_ADMIN"):
        raise HTTPException(status_code=409, detail="You cannot deactivate or demote your own administrator account.")
    if user.role == "COUNCIL_ADMIN" and user.is_active and (not payload.is_active or payload.role != "COUNCIL_ADMIN"):
        active_admins = db.scalar(select(func.count(User.id)).where(User.role == "COUNCIL_ADMIN", User.is_active.is_(True))) or 0
        if active_admins <= 1:
            raise HTTPException(status_code=409, detail="At least one active Council administrator must remain.")
    memberships = db.scalars(select(UserOrganization).where(UserOrganization.user_id == user.id)).all()
    if payload.organization_eins is not None:
        normalized_eins = list(dict.fromkeys(value.strip() for value in payload.organization_eins if value.strip()))
        organizations = db.scalars(select(Organization).where(
            Organization.ein.in_(normalized_eins), Organization.status == "ACTIVE"
        )).all() if normalized_eins else []
        if len(organizations) != len(normalized_eins):
            raise HTTPException(status_code=422, detail="One or more EINs do not identify an active organization.")
        db.execute(delete(UserOrganization).where(UserOrganization.user_id == user.id))
        for index, organization in enumerate(organizations):
            db.add(UserOrganization(user_id=user.id, organization_id=organization.id, is_primary=index == 0))
        memberships = []
    if payload.role == "EXTERNAL_SUBMITTER" and not (payload.organization_eins if payload.organization_eins is not None else memberships):
        raise HTTPException(status_code=422, detail="External submitters must have at least one organization assignment.")
    user.role = payload.role
    user.is_active = payload.is_active
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Account update conflicts with the database.") from exc
    db.refresh(user)
    organization_ids = list(db.scalars(select(UserOrganization.organization_id).where(UserOrganization.user_id == user.id)).all())
    return AdminUserResponse(id=user.id, email=user.email, full_name=user.full_name, role=user.role,
                             is_active=user.is_active, organization_ids=organization_ids)


@router.post("/{user_id}/reset-password", status_code=204)
def reset_password(
    user_id: str,
    payload: AdminPasswordResetRequest,
    _: User = Depends(require_roles("COUNCIL_ADMIN")),
    db: Session = Depends(get_db),
) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    try:
        user.password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.add(user)
    db.commit()

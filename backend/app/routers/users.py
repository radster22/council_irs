from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db import get_db
from app.models import User, UserOrganization
from app.schemas import AdminUserResponse

router = APIRouter(prefix="/api/admin/users", tags=["administration"])


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

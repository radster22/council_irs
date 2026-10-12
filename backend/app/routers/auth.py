from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_organization_ids, get_current_user
from app.core.security import create_access_token, verify_password
from app.db import get_db
from app.models import User
from app.schemas import AuthenticatedUserResponse, LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))

    if user is not None:
        if not user.is_active or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user.id, role=user.role)
    return TokenResponse(access_token=token, role=user.role, user_id=user.id, email=user.email)


@router.get("/me")
def me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthenticatedUserResponse:
    organization_ids = get_accessible_organization_ids(db, user.id)
    return AuthenticatedUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_ids=organization_ids,
    )

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.dependencies import get_accessible_organization_ids, require_organization_access, require_roles
from app.core.security import create_access_token, hash_password
from app.db import Base, get_db
from app.main import app
from app.models import Organization, User, UserOrganization


@pytest.fixture
def auth_context():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, expire_on_commit=False)

    with test_session() as db:
        db.add(
            User(
                id="user-1",
                email="submitter@example.org",
                password_hash=hash_password("LocalTestPassword123!"),
                full_name="Test Submitter",
                role="EXTERNAL_SUBMITTER",
                is_active=True,
            )
        )
        db.commit()

    def override_get_db():
        with test_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, test_session
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_login_checks_database_password_and_returns_database_role(auth_context) -> None:
    client, _ = auth_context

    response = client.post(
        "/api/auth/login",
        json={"email": "submitter@example.org", "password": "LocalTestPassword123!"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "EXTERNAL_SUBMITTER"
    assert response.json()["user_id"] == "user-1"


def test_unknown_demo_accounts_are_rejected_without_creating_database_users(auth_context) -> None:
    client, test_session = auth_context

    for email in ("submitter@council.local", "finance@council.local"):
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": "CouncilDemo123!"},
        )
        assert response.status_code == 401

    with test_session() as db:
        assert db.get(User, "demo-submitter") is None
        assert db.get(User, "demo-council-admin") is None


def test_login_rejects_invalid_password(auth_context) -> None:
    client, _ = auth_context

    response = client.post(
        "/api/auth/login",
        json={"email": "submitter@example.org", "password": "wrong-password"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize("payload", [{}, {"email": "submitter@example.org"}, {"password": "password"}])
def test_login_rejects_incomplete_credentials(auth_context, payload: dict[str, str]) -> None:
    client, _ = auth_context

    response = client.post("/api/auth/login", json=payload)

    assert response.status_code == 422


def test_me_rejects_missing_and_malformed_bearer_tokens(auth_context) -> None:
    client, _ = auth_context

    missing = client.get("/api/auth/me")
    malformed = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})

    assert missing.status_code == 401
    assert missing.headers["www-authenticate"] == "Bearer"
    assert malformed.status_code == 401
    assert malformed.json()["detail"] == "Invalid or expired token"


def test_me_rejects_expired_and_unknown_user_tokens(auth_context) -> None:
    client, _ = auth_context
    expired_token = jwt.encode(
        {
            "sub": "user-1",
            "role": "EXTERNAL_SUBMITTER",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    expired = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    unknown_user = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {create_access_token('missing-user')}"},
    )

    assert expired.status_code == 401
    assert expired.json()["detail"] == "Invalid or expired token"
    assert unknown_user.status_code == 401
    assert unknown_user.json()["detail"] == "User is unavailable"


def test_login_rejects_inactive_user(auth_context) -> None:
    client, test_session = auth_context
    with test_session() as db:
        user = db.get(User, "user-1")
        assert user is not None
        user.is_active = False
        db.commit()

    response = client.post(
        "/api/auth/login",
        json={"email": "submitter@example.org", "password": "LocalTestPassword123!"},
    )

    assert response.status_code == 401


def test_me_uses_current_database_role_and_organization_memberships(auth_context) -> None:
    client, test_session = auth_context
    with test_session() as db:
        db.add(Organization(id="org-1", ein="1234567890", legal_name="Test Org"))
        db.add(UserOrganization(user_id="user-1", organization_id="org-1", is_primary=True))
        db.commit()

    token = create_access_token("user-1", role="COUNCIL_ADMIN")
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["role"] == "EXTERNAL_SUBMITTER"
    assert response.json()["organization_ids"] == ["org-1"]


def test_role_and_organization_helpers_enforce_database_membership(auth_context) -> None:
    _, test_session = auth_context
    with test_session() as db:
        user = db.get(User, "user-1")
        assert user is not None
        with pytest.raises(HTTPException) as role_error:
            require_roles("COUNCIL_ADMIN")(user)
        assert role_error.value.status_code == 403

        db.add(Organization(id="org-1", ein="1234567890", legal_name="Test Org"))
        db.add(UserOrganization(user_id="user-1", organization_id="org-1", is_primary=True))
        db.commit()

        assert get_accessible_organization_ids(db, user.id) == ["org-1"]
        assert require_organization_access("org-1", user=user, db=db).organization_id == "org-1"
        with pytest.raises(HTTPException) as organization_error:
            require_organization_access("org-2", user=user, db=db)
        assert organization_error.value.status_code == 403


def test_user_administration_is_role_protected_and_reads_database_users(auth_context) -> None:
    client, test_session = auth_context
    external_token = create_access_token("user-1", role="COUNCIL_ADMIN")
    denied = client.get("/api/admin/users", headers={"Authorization": f"Bearer {external_token}"})
    assert denied.status_code == 403

    with test_session() as db:
        db.add(Organization(id="org-1", ein="1234567890", legal_name="Test Org"))
        db.add(UserOrganization(user_id="user-1", organization_id="org-1", is_primary=True))
        db.add(User(
            id="admin-1",
            email="admin@example.org",
            password_hash=hash_password("LocalTestPassword123!"),
            full_name="Council Admin",
            role="COUNCIL_ADMIN",
            is_active=True,
        ))
        db.commit()
    admin_token = create_access_token("admin-1", role="EXTERNAL_SUBMITTER")
    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "admin-1",
            "email": "admin@example.org",
            "full_name": "Council Admin",
            "role": "COUNCIL_ADMIN",
            "is_active": True,
            "organization_ids": [],
        },
        {
            "id": "user-1",
            "email": "submitter@example.org",
            "full_name": "Test Submitter",
            "role": "EXTERNAL_SUBMITTER",
            "is_active": True,
            "organization_ids": ["org-1"],
        },
    ]

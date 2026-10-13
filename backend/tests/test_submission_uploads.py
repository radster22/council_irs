from __future__ import annotations

import asyncio
import io
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db import Base, get_db
from app.main import app
from app.routers import submissions as submissions_router
from app.services import upload_service
from app.models import (
    Attachment,
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
from app.services.upload_service import save_uploaded_file
from app.services.submission_service import SubmissionError, validate_form_data


def test_upload_storage_root_is_repository_dot_uploads() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    assert upload_service.UPLOAD_ROOT == repository_root / ".uploads"


@pytest.fixture
def submission_context(tmp_path, monkeypatch):
    upload_root = tmp_path / "uploads"
    monkeypatch.setattr(upload_service, "UPLOAD_ROOT", upload_root)
    monkeypatch.setattr(submissions_router, "UPLOAD_ROOT", upload_root)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, expire_on_commit=False)

    with test_session() as db:
        user = User(
            id="user-1",
            email="submitter@example.org",
            password_hash=hash_password("LocalTestPassword123!"),
            full_name="Test Submitter",
            role="EXTERNAL_SUBMITTER",
            is_active=True,
        )
        organization = Organization(id="org-1", ein="1234567890", legal_name="Test Org")
        initiative = Initiative(id="initiative-1", code="TEST-1", name="Test Initiative", fiscal_year=2026)
        cycle = ReportingCycle(
            id="cycle-1",
            initiative_id="initiative-1",
            cycle_name="2026 Q1",
            start_date=date(2026, 1, 1),
            due_date=date(2026, 3, 31),
            status="OPEN",
        )
        assignment = InitiativeOrganization(
            initiative_id="initiative-1",
            organization_id="org-1",
            awarded_amount="1500.50",
        )
        template = FormTemplate(
            id="template-1",
            initiative_id="initiative-1",
            version=1,
            schema_definition={
                "sections": [{
                    "id": "program_metrics",
                    "name": "Programmatic Metrics",
                    "fields": [{"id": "agency_name", "label": "Agency name", "required": True}],
                }],
                "budget_reconciliation": {"target": "allocated_budget"},
            },
            is_published=True,
        )
        membership = UserOrganization(user_id="user-1", organization_id="org-1", is_primary=True)
        db.add_all([user, organization, initiative, cycle, assignment, template, membership])
        db.add(
            Submission(
                id="demo-report",
                initiative_id="initiative-1",
                organization_id="org-1",
                cycle_id="cycle-1",
                template_version=1,
                status="DRAFT",
                form_data={},
                allocated_budget="1500.50",
                total_budget="0.00",
                is_balanced=False,
                created_by="user-1",
            )
        )
        db.commit()

    def override_get_db():
        with test_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    token = create_access_token("user-1", role="EXTERNAL_SUBMITTER")
    try:
        with TestClient(app) as client:
            yield client, token, test_session
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_save_submission_accepts_valid_draft(submission_context) -> None:
    client, token, _ = submission_context

    response = client.post(
        "/api/submissions/demo-report/save",
        json={
            "status": "DRAFT",
            "form_data": {"initiative": "Youth Pipeline"},
            "budget_lines": [
                {"category": "Personnel", "amount": "1250.00"},
                {"category": "Operations", "amount": "250.50"},
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["submission_id"] == "demo-report"
    assert body["status"] == "DRAFT"
    assert body["total_budget"] == "1500.50"
    assert body["is_balanced"] is True
    assert body["is_valid"] is True


def test_save_submission_allows_empty_in_progress_draft(submission_context) -> None:
    client, token, _ = submission_context
    response = client.post(
        "/api/submissions/demo-report/save",
        json={"status": "DRAFT", "form_data": {}, "budget_lines": []},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["total_budget"] == "0.00"
    assert response.json()["is_balanced"] is False
    assert response.json()["line_count"] == 0


def test_submitter_dashboard_and_detail_are_scoped_to_member_organizations(submission_context) -> None:
    client, token, _ = submission_context
    listing = client.get("/api/submissions", headers={"Authorization": f"Bearer {token}"})
    assert listing.status_code == 200
    assert [item["submission_id"] for item in listing.json()] == ["demo-report"]

    detail = client.get("/api/submissions/demo-report", headers={"Authorization": f"Bearer {token}"})
    assert detail.status_code == 200
    assert detail.json()["form_schema"]["fields"][0]["id"] == "agency_name"


def test_save_submission_rejects_unscoped_submission_access(submission_context) -> None:
    client, token, test_session = submission_context

    with test_session() as db:
        db.add(Organization(id="org-2", ein="1234567891", legal_name="Other Org"))
        db.add(
            Submission(
                id="submission-1",
                initiative_id="initiative-1",
                organization_id="org-2",
                cycle_id="cycle-1",
                template_version=1,
                form_data={"report_name": "Test report"},
                allocated_budget=0,
                total_budget=0,
                is_balanced=False,
                created_by="user-1",
            )
        )
        db.commit()

    response = client.post(
        "/api/submissions/submission-1/save",
        json={
            "status": "DRAFT",
            "form_data": {"report_name": "Test report"},
            "budget_lines": [{"category": "Personnel", "amount": "125.00"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_upload_attachment_rejects_path_traversal_reference(submission_context) -> None:
    class FakeUpload:
        filename = "../escape.pdf"
        content_type = "application/pdf"

        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        async def read(self, size: int = -1) -> bytes:
            if size is None or size < 0:
                payload = self._payload
                self._payload = b""
                return payload
            chunk = self._payload[:size]
            self._payload = self._payload[size:]
            return chunk

    async def run_test() -> None:
        with pytest.raises(ValueError, match="Invalid submission"):
            await save_uploaded_file("../escape", FakeUpload(b"hello world"))

    asyncio.run(run_test())


def test_upload_attachment_requires_existing_authorized_submission(submission_context) -> None:
    client, token, _ = submission_context
    response = client.post(
        "/api/submissions/not-a-report/attachments",
        files={"file": ("report.pdf", io.BytesIO(b"contents"), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_upload_attachment_rejects_file_over_25mb(submission_context) -> None:
    client, token, _ = submission_context
    payload = b"x" * (26 * 1024 * 1024)

    response = client.post(
        "/api/submissions/demo-report/attachments",
        files={"file": ("large.csv", io.BytesIO(payload), "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 413
    assert "25 MB" in response.json()["detail"]


def test_upload_attachment_accepts_valid_file(submission_context) -> None:
    client, token, _ = submission_context

    response = client.post(
        "/api/submissions/demo-report/attachments",
        files={"file": ("report.pdf", io.BytesIO(b"%PDF-1.7\nTest document"), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["submission_id"] == "demo-report"
    assert body["original_filename"] == "report.pdf"
    assert body["file_size_bytes"] == len(b"%PDF-1.7\nTest document")
    assert body["attachment_id"]
    assert "stored_path" not in body

    with submission_context[2]() as db:
        attachment = db.query(Attachment).one()
        assert attachment.submission_id == "demo-report"
        assert attachment.file_size_bytes == len(b"%PDF-1.7\nTest document")

    download = client.get(
        f"/api/submissions/demo-report/attachments/{body['attachment_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert download.status_code == 200
    assert download.content == b"%PDF-1.7\nTest document"
    assert "report.pdf" in download.headers["content-disposition"]


def test_uploading_same_file_twice_creates_distinct_attachment_records(submission_context) -> None:
    client, token, test_session = submission_context
    for _ in range(2):
        response = client.post(
            "/api/submissions/demo-report/attachments",
            files={"file": ("report.pdf", io.BytesIO(b"%PDF-1.7\nsame contents"), "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    with test_session() as db:
        attachments = db.query(Attachment).order_by(Attachment.id).all()
        assert len(attachments) == 2
        assert attachments[0].object_key != attachments[1].object_key


def test_draft_autosave_preserves_blank_budget_cells_without_blocking(submission_context) -> None:
    client, token, test_session = submission_context
    response = client.post(
        "/api/submissions/demo-report/save",
        json={"status": "DRAFT", "form_data": {}, "budget_lines": [
            {"category": "", "description": "In progress", "amount": "", "actual_amount": ""},
        ]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["is_valid"] is False
    assert response.json()["validation_errors"]
    detail = client.get("/api/submissions/demo-report", headers={"Authorization": f"Bearer {token}"})
    assert detail.status_code == 200
    assert detail.json()["budget_lines"][0]["amount"] == ""
    assert detail.json()["form_data"] == {}
    with test_session() as db:
        line = db.query(BudgetLineItem).one()
        assert line.budgeted_amount == 0
        assert line.description == "In progress"


def test_upload_rejects_extension_and_mime_mismatch(submission_context) -> None:
    client, token, _ = submission_context
    response = client.post(
        "/api/submissions/demo-report/attachments",
        files={"file": ("report.pdf", io.BytesIO(b"contents"), "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "extension and content type" in response.json()["detail"]


def test_upload_rejects_content_that_does_not_match_declared_file_type(submission_context) -> None:
    client, token, _ = submission_context
    response = client.post(
        "/api/submissions/demo-report/attachments",
        files={"file": ("report.pdf", io.BytesIO(b"plain text pretending to be a PDF"), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "content does not match" in response.json()["detail"]


def test_council_admin_edit_creates_new_snapshot_and_audit_event(submission_context) -> None:
    client, _, test_session = submission_context
    with test_session() as db:
        db.add(User(id="admin-edit", email="admin-edit@example.org",
                    password_hash=hash_password("LocalTestPassword123!"), full_name="Council Admin",
                    role="COUNCIL_ADMIN", is_active=True))
        submission = db.get(Submission, "demo-report")
        assert submission is not None
        submission.status = "APPROVED"
        submission.form_data = {"agency_name": "Original Agency"}
        submission.total_budget = "1500.50"
        submission.is_balanced = True
        db.commit()
    token = create_access_token("admin-edit", role="COUNCIL_ADMIN")
    response = client.post("/api/submissions/demo-report/admin-edit", json={
        "form_data": {"agency_name": "Updated Agency"},
        "budget_lines": [{"category": "Personnel", "description": "Coordinator", "amount": "1500.50", "actual_amount": "1200.00"}],
        "comment": "Corrected based on approved financial documentation.",
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    with test_session() as db:
        version = db.query(SubmissionVersion).filter_by(submission_id="demo-report").one()
        assert version.form_snapshot == {"agency_name": "Updated Agency"}
        assert version.budget_snapshot["lines"][0]["actual_amount"] == "1200.00"
        assert version.reviewer_notes.startswith("Corrected")
        assert db.query(AuditLog).filter_by(submission_id="demo-report", action="ADMIN_EDIT").count() == 1
        line = db.query(BudgetLineItem).one()
        assert line.description == "Coordinator"
        assert line.actual_amount == 1200


def test_admin_rollover_clones_connected_configuration(submission_context) -> None:
    client, _, test_session = submission_context
    with test_session() as db:
        db.add(User(id="admin-rollover", email="rollover@example.org",
                    password_hash=hash_password("LocalTestPassword123!"), full_name="Council Admin",
                    role="COUNCIL_ADMIN", is_active=True))
        db.commit()
    token = create_access_token("admin-rollover", role="COUNCIL_ADMIN")
    response = client.post("/api/admin/rollover", json={
        "source_fiscal_year": 2026, "destination_fiscal_year": 2027,
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"initiatives_created": 1, "cycles_created": 1, "templates_created": 1, "assignments_created": 1}
    with test_session() as db:
        clone = db.query(Initiative).filter_by(fiscal_year=2027).one()
        assert clone.code == "TEST-1-FY2027"
        assert db.query(InitiativeOrganization).filter_by(initiative_id=clone.id).count() == 1
        cycle = db.query(ReportingCycle).filter_by(initiative_id=clone.id).one()
        assert cycle.status == "UPCOMING"
        assert cycle.start_date.year == 2027
        assert db.query(FormTemplate).filter_by(initiative_id=clone.id).count() == 1
        cycle_id = cycle.id
        initiative_id = clone.id
    opened = client.patch(f"/api/admin/cycles/{cycle_id}", json={"status": "OPEN"},
                          headers={"Authorization": f"Bearer {token}"})
    assert opened.status_code == 200
    retired = client.patch(f"/api/admin/initiatives/{initiative_id}", json={"status": "RETIRED"},
                           headers={"Authorization": f"Bearer {token}"})
    assert retired.status_code == 200


def test_admin_csv_export_is_a_downloadable_three_table_bundle(submission_context) -> None:
    client, _, test_session = submission_context
    with test_session() as db:
        db.add(User(id="admin-export", email="export@example.org",
                    password_hash=hash_password("LocalTestPassword123!"), full_name="Council Admin",
                    role="COUNCIL_ADMIN", is_active=True))
        db.commit()
    token = create_access_token("admin-export", role="COUNCIL_ADMIN")
    response = client.get("/api/admin/exports/csv", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as bundle:
        assert set(bundle.namelist()) == {"submissions.csv", "budget_line_items.csv", "attachments.csv"}


def test_admin_can_change_roles_and_reset_an_existing_password(submission_context) -> None:
    client, _, test_session = submission_context
    with test_session() as db:
        db.add(User(id="admin-users", email="users-admin@example.org",
                    password_hash=hash_password("LocalTestPassword123!"), full_name="Council Admin",
                    role="COUNCIL_ADMIN", is_active=True))
        db.commit()
    token = create_access_token("admin-users", role="COUNCIL_ADMIN")
    denied = client.patch("/api/admin/users/user-1", json={
        "role": "EXTERNAL_SUBMITTER", "is_active": True, "organization_eins": [],
    }, headers={"Authorization": f"Bearer {token}"})
    assert denied.status_code == 422
    updated = client.patch("/api/admin/users/user-1", json={
        "role": "COUNCIL_REVIEWER", "is_active": True, "organization_eins": [],
    }, headers={"Authorization": f"Bearer {token}"})
    assert updated.status_code == 200
    reset = client.post("/api/admin/users/user-1/reset-password", json={
        "password": "NewLocalPassword123!",
    }, headers={"Authorization": f"Bearer {token}"})
    assert reset.status_code == 204
    login = client.post("/api/auth/login", json={
        "email": "submitter@example.org", "password": "NewLocalPassword123!",
    })
    assert login.status_code == 200
    assert login.json()["role"] == "COUNCIL_REVIEWER"


def test_admin_can_create_organization_and_scoped_submitter(submission_context) -> None:
    client, _, test_session = submission_context
    with test_session() as db:
        db.add(User(id="admin-provision", email="provision-admin@example.org",
                    password_hash=hash_password("LocalTestPassword123!"), full_name="Council Admin",
                    role="COUNCIL_ADMIN", is_active=True))
        db.commit()
    token = create_access_token("admin-provision", role="COUNCIL_ADMIN")

    organization_response = client.post("/api/admin/organizations", json={
        "ein": "987654321", "legal_name": "New Test Organization", "org_type": "CBO", "borough": "Queens",
    }, headers={"Authorization": f"Bearer {token}"})
    assert organization_response.status_code == 201
    organization = organization_response.json()
    assert organization["ein"] == "98-7654321"

    account_response = client.post("/api/admin/users", json={
        "email": "new.submitter@example.org", "full_name": "New Submitter",
        "password": "NewLocalPassword123!", "role": "EXTERNAL_SUBMITTER",
        "organization_eins": [organization["ein"]],
    }, headers={"Authorization": f"Bearer {token}"})
    assert account_response.status_code == 201
    assert account_response.json()["organization_ids"] == [organization["id"]]

    login = client.post("/api/auth/login", json={
        "email": "new.submitter@example.org", "password": "NewLocalPassword123!",
    })
    assert login.status_code == 200
    assert login.json()["role"] == "EXTERNAL_SUBMITTER"


def test_admin_cannot_create_submitter_without_active_organization(submission_context) -> None:
    client, _, test_session = submission_context
    with test_session() as db:
        db.add(User(id="admin-provision-check", email="provision-check-admin@example.org",
                    password_hash=hash_password("LocalTestPassword123!"), full_name="Council Admin",
                    role="COUNCIL_ADMIN", is_active=True))
        db.commit()
    token = create_access_token("admin-provision-check", role="COUNCIL_ADMIN")
    response = client.post("/api/admin/users", json={
        "email": "unscoped.submitter@example.org", "full_name": "Unscoped Submitter",
        "password": "NewLocalPassword123!", "role": "EXTERNAL_SUBMITTER", "organization_eins": [],
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422


def test_review_queue_supports_registry_filters_and_explains_validation_errors(submission_context) -> None:
    client, _, test_session = submission_context
    with test_session() as db:
        organization = db.get(Organization, "org-1")
        assert organization is not None
        organization.borough = "Queens"
        db.add(User(id="review-filter", email="review-filter@example.org",
                    password_hash=hash_password("LocalTestPassword123!"), full_name="Council Reviewer",
                    role="COUNCIL_REVIEWER", is_active=True))
        db.commit()
    token = create_access_token("review-filter", role="COUNCIL_REVIEWER")

    response = client.get(
        "/api/submissions/review-queue?ein=1234&borough=Queens&fiscal_year=2026&initiative=Test%20Initiative&cycle=2026%20Q1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    item = response.json()[0]
    assert item["organization_ein"] == "1234567890"
    assert item["borough"] == "Queens"
    assert item["fiscal_year"] == 2026
    assert item["is_incomplete"] is True
    assert item["validation_errors"]
    no_match = client.get("/api/submissions/review-queue?ein=999999", headers={"Authorization": f"Bearer {token}"})
    assert no_match.status_code == 200
    assert no_match.json() == []


def test_admin_xlsx_export_produces_an_excel_workbook_when_dependencies_are_installed(submission_context) -> None:
    pytest.importorskip("pandas")
    pytest.importorskip("openpyxl")
    client, _, test_session = submission_context
    with test_session() as db:
        db.add(User(id="admin-xlsx", email="xlsx-admin@example.org",
                    password_hash=hash_password("LocalTestPassword123!"), full_name="Council Admin",
                    role="COUNCIL_ADMIN", is_active=True))
        db.commit()
    token = create_access_token("admin-xlsx", role="COUNCIL_ADMIN")
    response = client.get("/api/admin/exports/xlsx", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content.startswith(b"PK")


def test_admin_open_obligations_mark_past_due_assignments(submission_context) -> None:
    client, _, test_session = submission_context
    today = date.today()
    with test_session() as db:
        db.add(User(id="admin-obligations", email="obligations-admin@example.org",
                    password_hash=hash_password("LocalTestPassword123!"), full_name="Council Admin",
                    role="COUNCIL_ADMIN", is_active=True))
        db.add(ReportingCycle(
            id="overdue-cycle", initiative_id="initiative-1", cycle_name="Overdue cycle",
            start_date=today - timedelta(days=30), due_date=today - timedelta(days=1), status="OPEN",
        ))
        db.commit()

    token = create_access_token("admin-obligations", role="COUNCIL_ADMIN")
    response = client.get("/api/admin/obligations", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    obligation = next(item for item in response.json() if item["cycle_id"] == "overdue-cycle")
    assert obligation["is_overdue"] is True


def test_available_report_can_be_started_from_database_assignment(submission_context) -> None:
    client, token, test_session = submission_context
    with test_session() as db:
        db.add(
            ReportingCycle(
                id="cycle-2",
                initiative_id="initiative-1",
                cycle_name="2026 Q2",
                start_date=date(2026, 4, 1),
                due_date=date(2026, 6, 30),
                status="OPEN",
            )
        )
        db.commit()

    available = client.get("/api/submissions/available", headers={"Authorization": f"Bearer {token}"})
    assert available.status_code == 200
    assert len(available.json()) == 1
    assert available.json()[0]["organization_id"] == "org-1"

    response = client.post(
        "/api/submissions",
        json={"initiative_id": "initiative-1", "cycle_id": "cycle-2", "organization_id": "org-1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "DRAFT"
    assert response.json()["organization_id"] == "org-1"

    denied = client.post(
        "/api/submissions",
        json={"initiative_id": "initiative-1", "cycle_id": "cycle-2", "organization_id": "other-org"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert denied.status_code == 403


def test_submit_persists_snapshot_and_audit_record(submission_context) -> None:
    client, token, test_session = submission_context
    response = client.post(
        "/api/submissions/demo-report/save",
        json={
            "status": "SUBMITTED",
            "form_data": {"agency_name": "Test Agency"},
            "budget_lines": [{"category": "Personnel", "amount": "1500.50"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "SUBMITTED"

    with test_session() as db:
        version = db.query(SubmissionVersion).filter_by(submission_id="demo-report").one()
        assert version.form_snapshot == {"agency_name": "Test Agency"}
        assert db.query(AuditLog).filter_by(
            submission_id="demo-report", action="SUBMITTED"
        ).count() == 1


def test_submission_rejects_missing_required_template_field(submission_context) -> None:
    client, token, test_session = submission_context
    response = client.post(
        "/api/submissions/demo-report/save",
        json={
            "status": "SUBMITTED",
            "form_data": {},
            "budget_lines": [{"category": "Personnel", "amount": "1500.50"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "agency name" in response.json()["detail"].lower()

    with test_session() as db:
        submission = db.get(Submission, "demo-report")
        assert submission is not None
        assert submission.status == "DRAFT"
        assert db.query(SubmissionVersion).filter_by(submission_id="demo-report").count() == 0


def test_conditional_required_field_is_only_validated_when_visible() -> None:
    schema = {"fields": [
        {"id": "has_additional_program", "type": "boolean", "required": True},
        {"id": "additional_program_details", "type": "textarea", "required": True,
         "visible_when": {"field_id": "has_additional_program", "equals": True}},
    ]}

    validate_form_data(schema, {"has_additional_program": False})
    with pytest.raises(SubmissionError, match="Required field is missing: additional_program_details"):
        validate_form_data(schema, {"has_additional_program": True})


def test_submission_requires_budget_to_reconcile_to_allocated_amount(submission_context) -> None:
    client, token = submission_context[:2]
    response = client.post(
        "/api/submissions/demo-report/save",
        json={
            "status": "SUBMITTED",
            "form_data": {"agency_name": "Test Agency"},
            "budget_lines": [{"category": "Personnel", "amount": "1500.49"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "configured amount" in response.json()["detail"]


def test_council_review_queue_and_status_transitions_are_audited(submission_context) -> None:
    client, submitter_token, test_session = submission_context
    with test_session() as db:
        submission = db.get(Submission, "demo-report")
        assert submission is not None
        submission.status = "SUBMITTED"
        submission.form_data = {"agency_name": "Test Agency"}
        submission.total_budget = "1500.50"
        db.add(User(
            id="reviewer-1",
            email="reviewer@example.org",
            password_hash=hash_password("LocalTestPassword123!"),
            full_name="Council Reviewer",
            role="COUNCIL_REVIEWER",
            is_active=True,
        ))
        db.commit()
    reviewer_token = create_access_token("reviewer-1", role="COUNCIL_REVIEWER")

    denied = client.post(
        "/api/submissions/demo-report/review",
        json={"action": "START_REVIEW"},
        headers={"Authorization": f"Bearer {submitter_token}"},
    )
    assert denied.status_code == 403

    queue = client.get("/api/submissions/review-queue?status=SUBMITTED", headers={"Authorization": f"Bearer {reviewer_token}"})
    assert queue.status_code == 200
    assert queue.json()[0]["organization_name"] == "Test Org"

    started = client.post(
        "/api/submissions/demo-report/review",
        json={"action": "START_REVIEW", "comment": "Assigned for review"},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert started.status_code == 200
    assert started.json()["status"] == "IN_REVIEW"

    approved = client.post(
        "/api/submissions/demo-report/review",
        json={"action": "APPROVE", "comment": "Reviewed and approved"},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"

    with test_session() as db:
        audit = db.query(AuditLog).filter_by(submission_id="demo-report").order_by(AuditLog.id).all()
        assert [event.action for event in audit] == ["START_REVIEW", "APPROVE"]
        assert audit[-1].state_diff["comment"] == "Reviewed and approved"


def test_review_actions_reject_invalid_transitions(submission_context) -> None:
    client, _, test_session = submission_context
    with test_session() as db:
        db.add(User(
            id="reviewer-2",
            email="reviewer2@example.org",
            password_hash=hash_password("LocalTestPassword123!"),
            full_name="Council Reviewer",
            role="COUNCIL_REVIEWER",
            is_active=True,
        ))
        db.commit()
    token = create_access_token("reviewer-2", role="COUNCIL_REVIEWER")
    response = client.post(
        "/api/submissions/demo-report/review",
        json={"action": "APPROVE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409

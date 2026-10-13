from sqlalchemy import CheckConstraint, ForeignKeyConstraint

from app.db import Base
from app.models import Submission, SubmissionVersion


def test_models_match_all_live_table_names() -> None:
    assert set(Base.metadata.tables) == {
        "attachments",
        "audit_logs",
        "budget_line_items",
        "form_templates",
        "initiative_organizations",
        "initiative_relationships",
        "initiatives",
        "organizations",
        "reporting_cycles",
        "submission_versions",
        "submissions",
        "user_organizations",
        "users",
    }


def test_submission_composite_foreign_keys_preserve_scope() -> None:
    constraints = {
        constraint.name: (
            [column.name for column in constraint.columns],
            [element.target_fullname for element in constraint.elements],
        )
        for constraint in Submission.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }

    assert constraints["fk_sub_cycle_init"] == (
        ["initiative_id", "cycle_id"],
        ["reporting_cycles.initiative_id", "reporting_cycles.id"],
    )
    assert constraints["fk_sub_form_template"] == (
        ["initiative_id", "template_version"],
        ["form_templates.initiative_id", "form_templates.version"],
    )
    assert constraints["fk_sub_init_org"] == (
        ["initiative_id", "organization_id"],
        ["initiative_organizations.initiative_id", "initiative_organizations.organization_id"],
    )


def test_submission_versions_reference_submission_template_version() -> None:
    constraints = [
        constraint
        for constraint in SubmissionVersion.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    constraint = next(item for item in constraints if item.name == "fk_ver_sub_template")

    assert [column.name for column in constraint.columns] == ["submission_id", "template_version"]
    assert [element.target_fullname for element in constraint.elements] == [
        "submissions.id",
        "submissions.template_version",
    ]


def test_foreign_keys_preserve_restrictive_delete_rules() -> None:
    for table in Base.metadata.tables.values():
        for constraint in table.foreign_key_constraints:
            assert constraint.ondelete == "RESTRICT"
            assert constraint.onupdate == "NO ACTION"


def test_named_non_unique_indexes_match_live_schema() -> None:
    indexes = {
        table_name: {
            index.name: tuple(column.name for column in index.columns)
            for index in table.indexes
        }
        for table_name, table in Base.metadata.tables.items()
        if table.indexes
    }

    assert indexes == {
        "audit_logs": {
            "idx_audit_sub": ("submission_id",),
            "idx_audit_time": ("created_at",),
        },
        "initiatives": {"idx_init_fy": ("fiscal_year",)},
        "submissions": {"idx_sub_triage": ("is_balanced", "status")},
        "users": {"idx_user_role": ("role",)},
    }


def test_orm_declares_live_check_constraints() -> None:
    checks = {
        table_name: {constraint.name: str(constraint.sqltext) for constraint in table.constraints
                     if isinstance(constraint, CheckConstraint)}
        for table_name, table in Base.metadata.tables.items()
        if any(isinstance(constraint, CheckConstraint) for constraint in table.constraints)
    }

    assert checks == {
        "initiative_relationships": {"chk_rel_distinct": "predecessor_id <> successor_id"},
        "reporting_cycles": {"chk_cycle_dates": "start_date <= due_date"},
        "budget_line_items": {"chk_line_number": "line_number BETWEEN 1 AND 100"},
        "attachments": {"chk_att_size": "file_size_bytes > 0 AND file_size_bytes <= 26214400"},
    }

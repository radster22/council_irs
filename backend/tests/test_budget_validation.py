import pytest

from app.services.budget_service import validate_budget_lines


def test_validate_budget_lines_accepts_valid_budget() -> None:
    items = [
        {"category": "Personnel", "amount": "1500.00"},
        {"category": "Operations", "amount": "250.50"},
    ]

    summary = validate_budget_lines(items)

    assert summary["line_count"] == 2
    assert summary["total"] == "1750.50"
    assert summary["is_valid"] is True
    assert summary["errors"] == []


def test_validate_budget_lines_rejects_more_than_100_rows() -> None:
    items = [{"category": f"Category {index}", "amount": "1.00"} for index in range(101)]

    summary = validate_budget_lines(items)

    assert summary["is_valid"] is False
    assert any("100" in error for error in summary["errors"])


def test_validate_budget_lines_rejects_negative_amounts() -> None:
    summary = validate_budget_lines([
        {"category": "Personnel", "amount": "-10.00"},
    ])

    assert summary["is_valid"] is False
    assert any("non-negative" in error.lower() or "amount" in error.lower() for error in summary["errors"])


def test_validate_budget_lines_rejects_empty_budget() -> None:
    summary = validate_budget_lines([])

    assert summary["line_count"] == 0
    assert summary["total"] == "0.00"
    assert summary["is_valid"] is False
    assert "At least one budget line is required." in summary["errors"]


def test_validate_budget_lines_rejects_zero_total_budget() -> None:
    summary = validate_budget_lines([
        {"category": "Personnel", "amount": "0.00"},
        {"category": "Operations", "amount": "0.00"},
    ])

    assert summary["is_valid"] is False
    assert summary["total"] == "0.00"
    assert any("greater than zero" in error.lower() for error in summary["errors"])


def test_validate_budget_lines_rejects_blank_category_and_non_numeric_amount() -> None:
    summary = validate_budget_lines([
        {"category": "   ", "amount": "5.00"},
        {"category": "Operations", "amount": "abc"},
    ])

    assert summary["is_valid"] is False
    assert any("category is required" in error.lower() for error in summary["errors"])
    assert any("amount must be numeric" in error.lower() for error in summary["errors"])


def test_validate_budget_lines_accepts_single_valid_row() -> None:
    summary = validate_budget_lines([
        {"category": "Travel", "amount": "12.50"},
    ])

    assert summary["line_count"] == 1
    assert summary["total"] == "12.50"
    assert summary["is_valid"] is True
    assert summary["errors"] == []


def test_validate_budget_lines_rejects_non_finite_and_excess_precision_amounts() -> None:
    non_finite = validate_budget_lines([{"category": "Personnel", "amount": "NaN"}])
    excess_precision = validate_budget_lines([{"category": "Personnel", "amount": "1.001"}])

    assert non_finite["is_valid"] is False
    assert any("finite" in error.lower() for error in non_finite["errors"])
    assert excess_precision["is_valid"] is False
    assert any("two decimal places" in error.lower() for error in excess_precision["errors"])


def test_validate_budget_lines_allows_empty_draft_budget() -> None:
    summary = validate_budget_lines([], require_positive=False, require_category=False)

    assert summary["line_count"] == 0
    assert summary["total"] == "0.00"
    assert summary["is_valid"] is True
    assert summary["errors"] == []


def test_validate_budget_lines_rejects_amount_outside_live_decimal_precision() -> None:
    summary = validate_budget_lines([{"category": "Personnel", "amount": "1000000000000.00"}])

    assert summary["is_valid"] is False
    assert any("maximum" in error.lower() for error in summary["errors"])

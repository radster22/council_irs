from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Sequence

MAX_BUDGET_LINES = 100
MAX_BUDGET_AMOUNT = Decimal("999999999999.99")


def validate_budget_lines(
    lines: Sequence[dict[str, Any]] | Iterable[dict[str, Any]],
    *,
    require_positive: bool = True,
    require_category: bool = True,
) -> dict[str, Any]:
    normalized = list(lines)
    errors: list[str] = []
    total = Decimal("0.00")
    actual_total = Decimal("0.00")

    if not normalized and require_positive:
        return {
            "line_count": 0,
            "total": "0.00",
            "is_valid": False,
            "errors": ["At least one budget line is required."],
        }

    if len(normalized) > MAX_BUDGET_LINES:
        errors.append(f"Budget can contain at most {MAX_BUDGET_LINES} line items.")

    for index, item in enumerate(normalized, start=1):
        category = str(item.get("category", "")).strip()
        raw_amount = item.get("amount")
        if require_category and not category:
            errors.append(f"Line {index}: category is required.")
        if len(category) > 100:
            errors.append(f"Line {index}: category must be at most 100 characters.")

        try:
            amount = Decimal(str(raw_amount))
        except (InvalidOperation, TypeError, ValueError):
            errors.append(f"Line {index}: amount must be numeric.")
            continue

        if not amount.is_finite():
            errors.append(f"Line {index}: amount must be finite.")
            continue

        if amount < 0:
            errors.append(f"Line {index}: amount must be non-negative.")
            continue

        try:
            if amount.quantize(Decimal("0.01")) != amount:
                errors.append(f"Line {index}: amount can have at most two decimal places.")
                continue
            if amount > MAX_BUDGET_AMOUNT:
                errors.append(f"Line {index}: amount exceeds the supported maximum.")
                continue
        except InvalidOperation:
            errors.append(f"Line {index}: amount exceeds the supported precision.")
            continue

        if total + amount > MAX_BUDGET_AMOUNT:
            errors.append("Budget total exceeds the supported maximum.")
            continue
        total += amount

        raw_actual = item.get("actual_amount")
        if raw_actual not in (None, ""):
            try:
                actual = Decimal(str(raw_actual))
            except (InvalidOperation, TypeError, ValueError):
                errors.append(f"Line {index}: actual amount must be numeric.")
                continue
            if not actual.is_finite() or actual < 0:
                errors.append(f"Line {index}: actual amount must be finite and non-negative.")
                continue
            try:
                if actual.quantize(Decimal("0.01")) != actual or actual > MAX_BUDGET_AMOUNT:
                    errors.append(f"Line {index}: actual amount exceeds supported currency precision.")
                    continue
            except InvalidOperation:
                errors.append(f"Line {index}: actual amount exceeds supported precision.")
                continue
            actual_total += actual
            if actual_total > MAX_BUDGET_AMOUNT:
                errors.append("Actual budget total exceeds the supported maximum.")

    if require_positive and total <= 0:
        errors.append("Budget total must be greater than zero.")

    return {
        "line_count": len(normalized),
        "total": str(total.quantize(Decimal("0.01"))),
        "actual_total": str(actual_total.quantize(Decimal("0.01"))),
        "is_valid": not errors,
        "errors": errors,
    }

from __future__ import annotations

from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models import User
from app.schemas import BudgetValidationRequest, BudgetValidationResponse
from app.services.budget_service import validate_budget_lines

router = APIRouter(prefix="/api", tags=["budgets"])


@router.post("/budgets/validate", response_model=BudgetValidationResponse)
def validate_budget(payload: BudgetValidationRequest, _: User = Depends(get_current_user)) -> BudgetValidationResponse:
    summary = validate_budget_lines([line.model_dump() for line in payload.lines])
    return BudgetValidationResponse(**summary)

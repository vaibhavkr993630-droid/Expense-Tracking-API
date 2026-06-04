from pydantic import BaseModel, Field
from typing import List


class BudgetCreate(BaseModel):
    category: str = Field(description="Expense category (must match allowed categories)")
    amount: float = Field(gt=0, description="Budget limit for this category")
    month: int = Field(ge=1, le=12, description="Month (1-12)")
    year: int = Field(ge=2000, le=2100, description="Year e.g. 2025")


class BudgetResponse(BaseModel):
    id: int
    category: str
    amount: float
    month: int
    year: int

    model_config = {"from_attributes": True}


class BudgetAlert(BaseModel):
    category: str
    budget_limit: float
    spent: float
    remaining: float
    percentage_used: float
    status: str  # "ok" | "warning" | "exceeded"


class BudgetAlertsResponse(BaseModel):
    month: int
    year: int
    alerts: List[BudgetAlert]

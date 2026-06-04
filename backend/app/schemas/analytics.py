from pydantic import BaseModel
from typing import List


class MonthlySummary(BaseModel):
    year: int
    month: int
    total_expenses: float
    expense_count: int
    average_expense: float


class CategoryItem(BaseModel):
    category: str
    total: float
    count: int
    percentage: float


class CategoryBreakdownResponse(BaseModel):
    grand_total: float
    categories: List[CategoryItem]

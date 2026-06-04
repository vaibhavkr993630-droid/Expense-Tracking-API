from fastapi import APIRouter, Query, status
from sqlalchemy import func, extract
from app.dependencies.auth import user_dependency
from app.dependencies.database import db_dependency
from app.models.expense import Expense
from app.schemas.analytics import MonthlySummary, CategoryBreakdownResponse, CategoryItem
from typing import Optional


router = APIRouter(tags=["Analytics"])


@router.get("/expenses/summary/monthly", response_model=MonthlySummary, status_code=status.HTTP_200_OK)
async def monthly_summary(
    user: user_dependency,
    db: db_dependency,
    month: int = Query(..., ge=1, le=12, description="Month number (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Year e.g. 2024"),
):
    """
    ***Return a spending summary for a specific month and year.***

    **Args:**
        user (user_dependency): The current authenticated user.
        db (db_dependency): The database session.
        month (int): Month number, 1 to 12.
        year (int): Full year, e.g. 2024.

    **Returns:**
        MonthlySummary: total_expenses, expense_count, and average_expense.
        All values are 0 when no expenses exist for that period.
    """
    result = db.query(
        func.coalesce(func.sum(Expense.amount), 0).label("total"),
        func.count(Expense.id).label("count")
    ).filter(
        Expense.user_id == user.id,
        extract("month", Expense.date) == month,
        extract("year", Expense.date) == year
    ).first()

    total = float(result.total)
    count = int(result.count)
    average = round(total / count, 2) if count > 0 else 0.0

    return MonthlySummary(
        year=year,
        month=month,
        total_expenses=round(total, 2),
        expense_count=count,
        average_expense=average,
    )


@router.get("/expenses/summary/category", response_model=CategoryBreakdownResponse, status_code=status.HTTP_200_OK)
async def category_breakdown(
    user: user_dependency,
    db: db_dependency,
    month: Optional[int] = Query(None, ge=1, le=12, description="Optional month filter (1-12)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Optional year filter e.g. 2024"),
):
    """
    ***Return expenses grouped by category, with totals and percentages.***

    **Args:**
        user (user_dependency): The current authenticated user.
        db (db_dependency): The database session.
        month (int, optional): Filter results to a specific month.
        year (int, optional): Filter results to a specific year.

    **Returns:**
        CategoryBreakdownResponse: grand_total and a list of categories,
        each with its total, count, and percentage of the grand total.
    """
    query = db.query(
        Expense.category,
        func.sum(Expense.amount).label("total"),
        func.count(Expense.id).label("count"),
    ).filter(Expense.user_id == user.id)

    if month:
        query = query.filter(extract("month", Expense.date) == month)
    if year:
        query = query.filter(extract("year", Expense.date) == year)

    rows = query.group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).all()

    grand_total = float(sum(row.total for row in rows))

    categories = [
        CategoryItem(
            category=row.category,
            total=round(float(row.total), 2),
            count=int(row.count),
            percentage=round((float(row.total) / grand_total * 100), 2) if grand_total > 0 else 0.0,
        )
        for row in rows
    ]

    return CategoryBreakdownResponse(
        grand_total=round(grand_total, 2),
        categories=categories,
    )

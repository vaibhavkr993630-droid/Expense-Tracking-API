from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, extract
from app.dependencies.auth import user_dependency
from app.dependencies.database import db_dependency
from app.models.budget import Budget
from app.models.expense import Expense
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetAlertsResponse, BudgetAlert
from app.schemas.expense import ALLOWED_CATEGORIES
from typing import List
import datetime


router = APIRouter(tags=["Budgets"])


@router.post("/budgets", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def set_budget(user: user_dependency, budget: BudgetCreate, db: db_dependency):
    """
    ***Set or update a monthly budget for a specific category.***

    If a budget already exists for the same user/category/month/year, it is updated.
    """
    category = budget.category.title()
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Allowed: {', '.join(ALLOWED_CATEGORIES)}"
        )

    existing = db.query(Budget).filter(
        Budget.user_id == user.id,
        Budget.category == category,
        Budget.month == budget.month,
        Budget.year == budget.year,
    ).first()

    if existing:
        existing.amount = budget.amount
        db.commit()
        db.refresh(existing)
        return existing

    new_budget = Budget(
        user_id=user.id,
        category=category,
        amount=budget.amount,
        month=budget.month,
        year=budget.year,
    )
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget


@router.get("/budgets", response_model=List[BudgetResponse], status_code=status.HTTP_200_OK)
async def get_budgets(
    user: user_dependency,
    db: db_dependency,
    month: int = Query(None, ge=1, le=12, description="Filter by month (defaults to current month)"),
    year: int = Query(None, ge=2000, le=2100, description="Filter by year (defaults to current year)"),
):
    """
    ***Retrieve all budgets for a given month and year.***

    Defaults to the current month and year if not specified.
    """
    today = datetime.date.today()
    month = month or today.month
    year = year or today.year

    budgets = db.query(Budget).filter(
        Budget.user_id == user.id,
        Budget.month == month,
        Budget.year == year,
    ).all()

    return budgets


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(user: user_dependency, db: db_dependency, budget_id: int):
    """
    ***Delete a budget by its ID.***
    """
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user.id).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")
    db.delete(budget)
    db.commit()


@router.get("/budgets/alerts", response_model=BudgetAlertsResponse, status_code=status.HTTP_200_OK)
async def budget_alerts(
    user: user_dependency,
    db: db_dependency,
    month: int = Query(None, ge=1, le=12, description="Month to check (defaults to current month)"),
    year: int = Query(None, ge=2000, le=2100, description="Year to check (defaults to current year)"),
):
    """
    ***Compare actual spending against budgets and return alert statuses.***

    - **ok**: spent < 80% of budget
    - **warning**: spent >= 80% of budget
    - **exceeded**: spent > budget
    """
    today = datetime.date.today()
    month = month or today.month
    year = year or today.year

    budgets = db.query(Budget).filter(
        Budget.user_id == user.id,
        Budget.month == month,
        Budget.year == year,
    ).all()

    if not budgets:
        return BudgetAlertsResponse(month=month, year=year, alerts=[])

    spending_rows = db.query(
        Expense.category,
        func.sum(Expense.amount).label("total"),
    ).filter(
        Expense.user_id == user.id,
        extract("month", Expense.date) == month,
        extract("year", Expense.date) == year,
    ).group_by(Expense.category).all()

    spending_map = {row.category: float(row.total) for row in spending_rows}

    alerts = []
    for b in budgets:
        limit = float(b.amount)
        spent = spending_map.get(b.category, 0.0)
        percentage = round((spent / limit * 100), 2) if limit > 0 else 0.0
        remaining = round(limit - spent, 2)

        if spent > limit:
            alert_status = "exceeded"
        elif percentage >= 80:
            alert_status = "warning"
        else:
            alert_status = "ok"

        alerts.append(BudgetAlert(
            category=b.category,
            budget_limit=round(limit, 2),
            spent=round(spent, 2),
            remaining=remaining,
            percentage_used=percentage,
            status=alert_status,
        ))

    return BudgetAlertsResponse(month=month, year=year, alerts=alerts)

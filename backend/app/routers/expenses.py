from fastapi import APIRouter, HTTPException, status, Path, Query
from fastapi.responses import StreamingResponse
from app.dependencies.auth import user_dependency
from app.dependencies.database import db_dependency
from app.models.expense import Expense
from app.models.budget import Budget
from app.schemas.expense import AddExpense, UpdateExpense
from app.email_utils import send_budget_alert_email
from datetime import date, timedelta, datetime
from sqlalchemy import func, extract
import csv
import io
from fpdf import FPDF


router = APIRouter(
    tags=["Expenses"]
)


def _check_and_notify(user, db, month: int, year: int):
    budgets = db.query(Budget).filter(
        Budget.user_id == user.id,
        Budget.month == month,
        Budget.year == year,
    ).all()
    if not budgets:
        return

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
        pct = round(spent / limit * 100, 2) if limit > 0 else 0.0
        status_val = "exceeded" if spent > limit else ("warning" if pct >= 80 else "ok")
        alerts.append({
            "category": b.category,
            "budget_limit": round(limit, 2),
            "spent": round(spent, 2),
            "remaining": round(limit - spent, 2),
            "percentage_used": pct,
            "status": status_val,
        })

    send_budget_alert_email(user.email, user.username, alerts, month, year)


# Read all expenses
@router.get("/expenses", status_code=status.HTTP_200_OK)
async def read_expenses(
    user: user_dependency,
    db: db_dependency,
    from_date: date = Query(None, description="Filter expenses from this date (YYYY-MM-DD)"),
    to_date: date = Query(None, description="Filter expenses up to this date (YYYY-MM-DD)"),
    period: str = Query(None, description="Predefined period: 'week', 'month', '3months'"),
    page: int = Query(1, ge=1, description="Page number, starts at 1"),
    limit: int = Query(10, ge=1, le=100, description="Results per page (max 100)"),
):
    """
    ***Retrieve all expenses for the authenticated user with optional date filters and pagination.***

    **Args:**
        user (user_dependency): The current authenticated user.
        db (db_dependency): The database session.
        from_date (date, optional): Start date to retrieve expenses from this date onward.
        to_date (date, optional): End date to retrieve expenses up to this date.
        period (str, optional): Predefined period — 'week', 'month', or '3months'.
        page (int): Page number for pagination, starts at 1.
        limit (int): Number of results per page, between 1 and 100.

    **Raises:**
        HTTPException: If from_date is later than to_date.
        HTTPException: If an invalid period is provided.

    **Returns:**
        dict: expenses list, current page, limit, and total count.
    """
    # Feature 3: Date range validation — reject reversed ranges with a clear error
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'from_date' cannot be later than 'to_date'."
        )

    # Feature 4: Base query is always scoped to the logged-in user — user isolation
    query = db.query(Expense).filter(Expense.user_id == user.id)

    # Predefined period filter
    if period:
        period_map = {
            "week": timedelta(days=7),
            "month": timedelta(days=30),
            "3months": timedelta(days=90)
        }
        period_lower = period.lower()
        if period_lower in period_map:
            from_date = datetime.now().date() - period_map[period_lower]
            to_date = datetime.now().date()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 'period' value. Accepted values are 'week', 'month', '3months'.")

    # Apply date range filters
    if from_date:
        query = query.filter(Expense.date >= from_date)
    if to_date:
        query = query.filter(Expense.date <= to_date)

    # Feature 5: Count total matching records before applying pagination
    total = query.count()

    # Feature 5: Apply pagination — skip (page-1)*limit rows, then take 'limit' rows
    expenses = query.order_by(Expense.date.desc()).offset((page - 1) * limit).limit(limit).all()

    return {
        "expenses": expenses,
        "page": page,
        "limit": limit,
        "total": total,
    }



# Add expense
@router.post("/expenses", status_code=status.HTTP_201_CREATED)
async def add_expense(user: user_dependency, expense: AddExpense, db: db_dependency):
    """
    ***Add a new expense for the authenticated user.***

    **Args:**
        user (user_dependency): The current authenticated user.
        expense (AddExpense): The details of the expense to be added.
        db (db_dependency): The database session.

    **Returns:**
        dict: A dictionary with a success message and the ID of the created expense.
    """
    new_expense = Expense(
        user_id=user.id,
        amount=expense.amount,
        category=expense.category,
        description=expense.description,
        date=expense.date
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    _check_and_notify(user, db, new_expense.date.month, new_expense.date.year)

    return {"message": f"Expense ${new_expense.amount} added.", "id": new_expense.id}



# Update expense
@router.put("/expenses/{id}", status_code=status.HTTP_200_OK)
async def update_expense(user: user_dependency, expense: UpdateExpense, db: db_dependency, id: int = Path(gt=0)):
    """
    ***Update an existing expense for the authenticated user.***

    **Args:**
        user (user_dependency): The current authenticated user.
        expense (UpdateExpense): The details of the expense to be updated.
        db (db_dependency): The database session.
        id (int, optional): The ID of the expense to be updated. Defaults to Path(gt=0).

    **Raises:**
        HTTPException: If the expense doesn't exist or doesn't belong to the user.

    **Returns:**
        dict: A success message indicating that the expense was updated.
    """
    check_expense = db.query(Expense).filter(Expense.id == id, Expense.user_id == user.id).first()

    if not check_expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The expense doesn't exist.")

    for key, value in vars(expense).items():
        if value is not None:
            setattr(check_expense, key, value)

    db.add(check_expense)
    db.commit()
    db.refresh(check_expense)

    _check_and_notify(user, db, check_expense.date.month, check_expense.date.year)

    return {"message": f"Expense with ID {id} successfully updated."}



# Export expenses as CSV
@router.get("/expenses/export/csv", status_code=status.HTTP_200_OK)
async def export_expenses_csv(
    user: user_dependency,
    db: db_dependency,
    from_date: date = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: date = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query(None, description="Predefined period: 'week', 'month', '3months'"),
):
    """
    ***Export all expenses as a downloadable CSV file.***

    Supports the same date filters as the GET /expenses endpoint.
    """
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'from_date' cannot be later than 'to_date'.")

    query = db.query(Expense).filter(Expense.user_id == user.id)

    if period:
        period_map = {"week": timedelta(days=7), "month": timedelta(days=30), "3months": timedelta(days=90)}
        if period.lower() in period_map:
            from_date = datetime.now().date() - period_map[period.lower()]
            to_date = datetime.now().date()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 'period' value.")

    if from_date:
        query = query.filter(Expense.date >= from_date)
    if to_date:
        query = query.filter(Expense.date <= to_date)

    expenses = query.order_by(Expense.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Date", "Category", "Amount", "Description"])
    for exp in expenses:
        writer.writerow([
            exp.id,
            str(exp.date)[:10],
            exp.category,
            float(exp.amount),
            exp.description or "",
        ])

    output.seek(0)
    filename = f"expenses_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# Export expenses as PDF
@router.get("/expenses/export/pdf", status_code=status.HTTP_200_OK)
async def export_expenses_pdf(
    user: user_dependency,
    db: db_dependency,
    from_date: date = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: date = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query(None, description="Predefined period: 'week', 'month', '3months'"),
):
    """
    ***Export all expenses as a downloadable PDF file.***

    Supports the same date filters as the GET /expenses endpoint.
    """
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'from_date' cannot be later than 'to_date'.")

    query = db.query(Expense).filter(Expense.user_id == user.id)

    if period:
        period_map = {"week": timedelta(days=7), "month": timedelta(days=30), "3months": timedelta(days=90)}
        if period.lower() in period_map:
            from_date = datetime.now().date() - period_map[period.lower()]
            to_date = datetime.now().date()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 'period' value.")

    if from_date:
        query = query.filter(Expense.date >= from_date)
    if to_date:
        query = query.filter(Expense.date <= to_date)

    expenses = query.order_by(Expense.date.desc()).all()
    total = sum(float(e.amount) for e in expenses)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Expense Report", ln=True, align="C")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  User: {user.username}", ln=True, align="C")
    if from_date or to_date:
        period_label = f"{from_date or 'start'} to {to_date or 'today'}"
        pdf.cell(0, 6, f"Period: {period_label}", ln=True, align="C")
    pdf.ln(4)

    # Table header
    pdf.set_fill_color(67, 97, 238)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    col_widths = [20, 28, 35, 28, 79]
    headers = ["#", "Date", "Category", "Amount", "Description"]
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 8, h, border=1, fill=True)
    pdf.ln()

    # Table rows
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=9)
    for i, exp in enumerate(expenses):
        fill = i % 2 == 0
        pdf.set_fill_color(240, 240, 255) if fill else pdf.set_fill_color(255, 255, 255)
        desc = (exp.description or "")[:45]
        row = [str(exp.id), str(exp.date)[:10], exp.category, f"${float(exp.amount):.2f}", desc]
        for w, val in zip(col_widths, row):
            pdf.cell(w, 7, val, border=1, fill=True)
        pdf.ln()

    # Total row
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230, 230, 255)
    pdf.cell(sum(col_widths[:3]), 8, "TOTAL", border=1, fill=True)
    pdf.cell(col_widths[3], 8, f"${total:.2f}", border=1, fill=True)
    pdf.cell(col_widths[4], 8, f"{len(expenses)} expense(s)", border=1, fill=True)
    pdf.ln()

    pdf_bytes = pdf.output()
    filename = f"expenses_{datetime.now().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        iter([bytes(pdf_bytes)]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# Delete expense
@router.delete("/expenses/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(user: user_dependency, id: int, db: db_dependency):
    """
    ***Delete an expense for the authenticated user.***

    **Args:**
        user (user_dependency): The current authenticated user.
        id (int): The ID of the expense to be deleted.
        db (db_dependency): The database session.

    **Raises:**
        HTTPException: If the expense doesn't exist or the user doesn't have permission to delete it.
    """
    to_delete = db.query(Expense).filter(Expense.id == id, Expense.user_id == user.id).first()

    if not to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The expense doesn't exist or you don't have permission to delete it.")

    db.delete(to_delete)
    db.commit()

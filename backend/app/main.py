from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.db import engine
from app.limiter import limiter
from app.models.user import User
from app.models.expense import Expense
from app.models.budget import Budget
from app.routers import health, auth, expenses, users, analytics, budgets


app = FastAPI(
    title="Expense Tracker API",
    version="2.0.0",
    description="""A comprehensive API designed for managing personal expenses,
                enabling users to register and log in securely using JWT-based authentication,
                as well as add, update, and delete expenses with ease.
                The API also allows users to filter and retrieve their expenses based on various criteria,
                export data as CSV/PDF, set monthly budgets with spending alerts,
                and manage their profiles for a personalized experience.""",
    contact={
        "name": "vaibhavkr993630-droid",
        "url": "https://github.com/vaibhavkr993630-droid",
        "email": "vaibhav.kr993630@gmail.com"
    }
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — allow the frontend to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Create all database tables
User.metadata.create_all(bind=engine)
Expense.metadata.create_all(bind=engine)
Budget.metadata.create_all(bind=engine)

# All API routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(users.router)
app.include_router(analytics.router)
app.include_router(budgets.router)

# --- Static file serving for the React SPA ---
# __file__ = backend/app/main.py → .parent.parent.parent = project root
DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"

if DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_root():
        return FileResponse(str(DIST / "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(DIST / "index.html"))
else:
    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": "Expense Tracker API is running. Build the React frontend to see the UI."}

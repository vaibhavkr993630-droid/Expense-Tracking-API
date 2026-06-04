# Expense Tracker API

A modern, production-ready expense tracking application with intelligent budget management, real-time spending alerts, and advanced analytics.

## What Makes It Different

Unlike basic expense trackers, this application includes:

- **Smart Budget Alerts** — Get email notifications when spending approaches or exceeds monthly category budgets
- **Real-Time Analytics** — Visual dashboard showing spending trends, category breakdowns, and monthly comparisons
- **Professional Data Export** — Download expenses as formatted PDF documents or CSV files for accounting and analysis
- **Rate-Limited API** — Production-grade API with request throttling to ensure reliability
- **Full Authentication System** — Secure JWT-based authentication with bcrypt password hashing
- **Enterprise-Ready Deployment** — Docker containerization, PostgreSQL database, and CI/CD pipeline

## Key Features

✅ Create, track, and manage expenses with categories and notes  
✅ Set monthly budgets per category with automatic alerts  
✅ Visualize spending patterns with analytics charts  
✅ Export data as PDF or CSV  
✅ Email notifications for budget warnings and exceeded alerts  
✅ Secure authentication with JWT tokens  
✅ Rate-limited API for reliability  
✅ Responsive React UI with TailwindCSS  
✅ Docker-ready deployment  
✅ Automated testing with GitHub Actions CI/CD  

## Tech Stack

**Backend:** FastAPI, PostgreSQL, SQLAlchemy, JWT  
**Frontend:** React 18, Vite, TailwindCSS, Axios  
**DevOps:** Docker, Docker Compose, GitHub Actions  
**Features:** APScheduler (email), fpdf2 (PDF export), slowapi (rate limiting)

## Quick Start

**Clone & Run:**
```bash
git clone https://github.com/vaibhavkr993630-droid/Expense-Tracker-API.git
cd Expense-Tracker-API
docker compose up -d
```

**API Documentation:** http://localhost:8000/docs  
**Frontend:** http://localhost:3000

## Architecture

- **Backend:** FastAPI REST API with PostgreSQL + SQLAlchemy ORM
- **Frontend:** React 18 SPA with React Router and TailwindCSS
- **Database:** PostgreSQL with migrations and indexed queries
- **Auth:** JWT tokens with bcrypt password hashing
- **Deployment:** Docker containers with GitHub Actions CI/CD

## Use Cases

Perfect for:
- Personal finance management and budgeting
- Expense tracking with category analytics
- Learning modern web development (FastAPI + React)
- Building production-ready full-stack applications
- DevOps practice with Docker and CI/CD

## License

MIT

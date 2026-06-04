# Expense Tracker API

A full-stack web application for tracking personal expenses with advanced features including budget management, analytics, PDF/CSV exports, and real-time spending alerts.

## Features

- **User Authentication** — JWT-based secure authentication with bcrypt password hashing
- **Expense Management** — Create, read, update, delete expenses with category and date filtering
- **Budget Tracking** — Set monthly budgets per category with spending alerts
- **Analytics Dashboard** — Visualize spending patterns with charts and category breakdowns
- **Data Export** — Download expenses as PDF or CSV files
- **Rate Limiting** — API request throttling to prevent abuse
- **Email Notifications** — Receive alerts when spending exceeds budget
- **Responsive UI** — React + TailwindCSS frontend with modern design
- **Docker Support** — Containerized PostgreSQL and FastAPI backend
- **CI/CD Pipeline** — Automated testing and deployment with GitHub Actions

## Tech Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Authentication:** JWT + bcrypt
- **Rate Limiting:** slowapi
- **PDF Generation:** fpdf2
- **Task Scheduling:** APScheduler (for email notifications)

### Frontend
- **Framework:** React 18 with Vite
- **Styling:** TailwindCSS
- **HTTP Client:** Axios
- **State Management:** React Context API

### DevOps
- **Containerization:** Docker & Docker Compose
- **CI/CD:** GitHub Actions
- **Database:** PostgreSQL (Docker or native)

## Project Structure

```
Expense-Tracker-API/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy ORM models (User, Expense, Budget)
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── routers/         # API route handlers
│   │   ├── dependencies/    # Auth, JWT, database dependencies
│   │   ├── main.py          # FastAPI app initialization
│   │   └── db.py            # Database connection
│   ├── tests/               # Pytest unit tests
│   ├── requirements.txt     # Python dependencies
│   └── alembic/             # Database migrations
├── frontend/
│   ├── src/
│   │   ├── pages/           # React page components
│   │   ├── components/      # Reusable UI components
│   │   ├── api/             # API client configuration
│   │   ├── context/         # Auth context provider
│   │   └── App.jsx          # Main app component
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml       # PostgreSQL + backend services
└── Dockerfile               # Multi-stage build for production
```

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+ (or use Docker)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/vaibhavkr993630-droid/Expense-Tracker-API.git
   cd Expense-Tracker-API
   ```

2. **Set up PostgreSQL** (using Docker Compose)
   ```bash
   docker compose up -d
   ```
   Or install PostgreSQL natively and create:
   ```bash
   sudo -u postgres psql -c "CREATE USER expenseuser WITH PASSWORD 'expensepass';"
   sudo -u postgres psql -c "CREATE DATABASE expense_tracker OWNER expenseuser;"
   ```

3. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   export PYTHONPATH=.
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your configuration:
   ```
   DATABASE_URL=postgresql://expenseuser:expensepass@localhost:5432/expense_tracker
   SECRET_KEY=your-strong-random-key-32-chars-minimum
   ```

5. **Run Backend Server**
   ```bash
   PYTHONPATH=. python -m uvicorn app.main:app --reload
   ```
   Server runs on `http://localhost:8000`

6. **Frontend Setup** (in a new terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   App runs on `http://localhost:5173`

### API Documentation

Once the backend is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### API Endpoints

#### Authentication
- `POST /auth/register` — Create new user account
- `POST /auth/login` — Login and get JWT token
- `POST /auth/refresh` — Refresh expired token

#### Expenses
- `GET /expenses` — List all user expenses (with filtering)
- `POST /expenses` — Create new expense
- `PUT /expenses/{id}` — Update expense
- `DELETE /expenses/{id}` — Delete expense
- `GET /expenses/export/csv` — Download CSV file
- `GET /expenses/export/pdf` — Download PDF file

#### Budgets
- `GET /budgets` — List user budgets
- `POST /budgets` — Set/update budget
- `DELETE /budgets/{id}` — Delete budget
- `GET /budgets/alerts` — Get spending alerts

#### Analytics
- `GET /analytics/summary` — Get expense summary by category
- `GET /analytics/trends` — Get monthly spending trends

#### Health
- `GET /health` — API health check

## Database Schema

### Users
```sql
- id (primary key)
- username (unique)
- email (unique)
- password_hash (bcrypt)
- created_at
```

### Expenses
```sql
- id (primary key)
- user_id (foreign key)
- amount (decimal)
- category (string)
- description (text)
- date (date)
- created_at
```

### Budgets
```sql
- id (primary key)
- user_id (foreign key)
- category (string)
- amount (decimal)
- month (integer)
- year (integer)
- unique constraint: (user_id, category, month, year)
```

## Testing

Run the test suite:
```bash
cd backend
pytest tests/
```

Run with coverage:
```bash
pytest --cov=app tests/
```

## Deployment

### Docker
Build and run with Docker Compose:
```bash
docker compose up -d
```

Access at `http://localhost:8000`

### Railway / Cloud Deployment

1. Push to GitHub
2. Go to https://railway.app
3. Create new project → Deploy from GitHub repo
4. Select this repository
5. Railway auto-creates PostgreSQL and deploys the app
6. Set environment variables in Railway dashboard

## Environment Variables

Required in `.env`:
- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — JWT signing key (minimum 32 characters)

Optional:
- `SMTP_SERVER` — Email server for notifications
- `SMTP_PORT` — Email port
- `SMTP_USER` — Email account username
- `SMTP_PASSWORD` — Email account password

## Performance Features

- **Rate Limiting** — 100 requests per minute per IP
- **Database Indexing** — Optimized queries on user_id, category, date
- **JWT Tokens** — Stateless authentication (no session database needed)
- **Connection Pooling** — Reusable database connections

## Security

- Passwords hashed with bcrypt (4.0.1)
- JWT tokens with configurable expiration
- CORS protection
- Environment variables for sensitive data
- SQL injection prevention via SQLAlchemy ORM
- XSS protection in React frontend

## License

This project is open source and available under the MIT License.

## Contact

For questions or feedback, reach out at `vaibhav.kr993630@gmail.com`

---

**Built with FastAPI, React, and PostgreSQL**

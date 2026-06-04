# ── Stage 1: Build React frontend ─────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --prefer-offline

COPY frontend/ .
RUN npm run build


# ── Stage 2: Python API ────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend source (lives at /app/backend/app/)
COPY backend/app/ ./backend/app/

# React build output (lives at /app/frontend/dist/)
# main.py resolves Path(__file__).parent.parent.parent → /app → finds /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# PYTHONPATH lets Python find the 'app' package inside backend/
ENV PYTHONPATH=/app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

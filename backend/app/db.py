import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# Load backend/.env explicitly
# Path(__file__) = backend/app/db.py → .parent.parent = backend/
load_dotenv(Path(__file__).parent.parent / ".env")


# PostgreSQL connection URL from environment
URL = os.getenv("DATABASE_URL")

if not URL:
    raise ValueError("DATABASE_URL is not set. Check backend/.env")


# Create the PostgreSQL engine
engine = create_engine(URL)


# Session factory — one session per request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class for all models
Base = declarative_base()

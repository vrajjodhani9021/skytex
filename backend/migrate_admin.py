"""Run once to create PostgreSQL tables and seed data if needed."""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

try:
    from backend.database import init_db
except ImportError:
    from database import init_db

if __name__ == "__main__":
    init_db()
    print("Database migrated. Admin user ready (see .env.example for credentials).")

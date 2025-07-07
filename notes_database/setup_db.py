"""
Setup script for SecureNoteHub database.
Runs the initial migration to create tables if not exists.
"""

import os
from sqlalchemy import create_engine
from models import Base

# PUBLIC_INTERFACE
def setup_database():
    """
    Bootstraps the database—creates all tables (no-op if already present).
    Reads the NOTES_DATABASE_URL from environment or defaults to local SQLite.
    """
    db_url = os.environ.get("NOTES_DATABASE_URL", "sqlite:///./notes_app.db")
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    print("Database setup complete (all tables created if not present).")

if __name__ == "__main__":
    setup_database()

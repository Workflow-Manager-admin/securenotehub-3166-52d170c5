"""
Alembic initial migration: create users and notes tables.
Run this migration to initialize the database schema.
"""

from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, ForeignKey, Text
from datetime import datetime
from sqlalchemy import create_engine

# PUBLIC_INTERFACE
def create_initial_tables(engine):
    """Create the users and notes tables on the current engine."""
    metadata = MetaData()

    users = Table(
        "users", metadata,
        Column("id", Integer, primary_key=True, index=True),
        Column("email", String(255), nullable=False, unique=True, index=True),
        Column("password_hash", String(255), nullable=False),
        Column("created_at", DateTime, default=datetime.utcnow),
    )

    notes = Table(
        "notes", metadata,
        Column("id", Integer, primary_key=True, index=True),
        Column("title", String(255), nullable=False),
        Column("content", Text, nullable=True),
        Column("owner_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        Column("created_at", DateTime, default=datetime.utcnow),
        Column("updated_at", DateTime, default=datetime.utcnow),
    )

    metadata.create_all(engine)

if __name__ == "__main__":
    # You may set NOTES_DATABASE_URL in the environment (.env) with something like:
    # NOTES_DATABASE_URL=sqlite:///./notes_app.db
    import os
    from sqlalchemy.engine.url import make_url

    db_url = os.environ.get("NOTES_DATABASE_URL", "sqlite:///./notes_app.db")
    engine = create_engine(db_url)
    create_initial_tables(engine)
    print("Database tables created.")

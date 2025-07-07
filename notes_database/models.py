"""
Database models for SecureNoteHub notes app.
Defines User and Note SQLAlchemy ORM models.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# PUBLIC_INTERFACE
class User(Base):
    """
    User account model for SecureNoteHub.

    Fields:
        id: Integer primary key.
        email: Unique email address (used for authentication).
        password_hash: Hashed password.
        created_at: Timestamp of user creation.
        notes: Relationship to Note model.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")


# PUBLIC_INTERFACE
class Note(Base):
    """
    Note model for SecureNoteHub.

    Fields:
        id: Integer primary key.
        title: Title of the note.
        content: The note's content.
        owner_id: Foreign key to users table.
        created_at: Timestamp of note creation.
        updated_at: Timestamp of last update.
        owner: Relationship to User model.
    """
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="notes")

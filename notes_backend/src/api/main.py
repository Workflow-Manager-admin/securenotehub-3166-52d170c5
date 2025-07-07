"""
FastAPI backend for SecureNoteHub.

Provides RESTful API endpoints for:
- User registration and login (JWT-based authentication)
- Notes CRUD (Create, Read, Update, Delete) for authenticated users

Uses the shared SQLAlchemy models from notes_database for User and Note.

Environment variable configuration:
- NOTES_DATABASE_URL: SQLAlchemy connection string (default: sqlite:///../notes_app.db)
- JWT_SECRET_KEY: Secret for signing JWTs (required for security in production)
- JWT_ALGORITHM: Algorithm for JWT (default: HS256)
- ACCESS_TOKEN_EXPIRE_MINUTES: JWT token lifetime (default: 60)

See the README and .env.example for sample configuration and usage.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy import create_engine
import os
from datetime import datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr
from jose import jwt, JWTError
from passlib.context import CryptContext

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../notes_database/")))
from models import User, Note

# === Configuration ===
NOTES_DATABASE_URL = os.getenv("NOTES_DATABASE_URL", "sqlite:///../notes_app.db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "insecure-placeholder-secret")  # Replace in production!
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Database setup
engine = create_engine(NOTES_DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in NOTES_DATABASE_URL else {})
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal = scoped_session(SessionFactory)

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

openapi_tags = [
    {"name": "auth", "description": "Authentication/registration endpoints"},
    {"name": "notes", "description": "CRUD for notes (requires authentication)"},
]

app = FastAPI(
    title="SecureNoteHub - Notes Backend",
    description="RESTful API for notes and user authentication.",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You may scope this to your frontend domain for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Dependency ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Pydantic schemas ===

# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """Registration payload schema."""
    email: EmailStr = Field(..., description="Email for registration")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")

# PUBLIC_INTERFACE
class UserOut(BaseModel):
    """User info returned (never includes password)."""
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class Token(BaseModel):
    """JWT token response schema."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")

# PUBLIC_INTERFACE
class NoteCreate(BaseModel):
    """POST payload for creating notes."""
    title: str = Field(..., min_length=1, max_length=255, description="Note title")
    content: Optional[str] = Field(default="", description="Note content (text)")

# PUBLIC_INTERFACE
class NoteUpdate(BaseModel):
    """PATCH payload for updating notes."""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Optional new title")
    content: Optional[str] = Field(None, description="Optional new content")

# PUBLIC_INTERFACE
class NoteOut(BaseModel):
    """Returned note schema."""
    id: int
    title: str
    content: str
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# === Auth utils ===

# PUBLIC_INTERFACE
def verify_password(plain_password, password_hash):
    """Returns True if the password matches the hash."""
    return pwd_context.verify(plain_password, password_hash)

# PUBLIC_INTERFACE
def get_password_hash(password):
    """Hash a password for storing."""
    return pwd_context.hash(password)

# PUBLIC_INTERFACE
def create_access_token(*, data: dict, expires_delta: timedelta = None):
    """
    Returns a JWT token encoding the provided data.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# PUBLIC_INTERFACE
def get_user_by_email(db: Session, email: str):
    """Returns User instance for email, or None."""
    return db.query(User).filter(User.email == email).first()

# PUBLIC_INTERFACE
def authenticate_user(db: Session, email: str, password: str):
    """Authenticate user; return user if valid, else None."""
    user = get_user_by_email(db, email)
    if user and verify_password(password, user.password_hash):
        return user
    return None

# PUBLIC_INTERFACE
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency: Extract user based on provided JWT token.
    Throws HTTPException on authentication failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

# === API ROUTES ===

@app.get("/", tags=["root"])
def health_check():
    """API health check."""
    return {"message": "Healthy"}

# --- AUTH Endpoints ---

@app.post("/auth/register", response_model=UserOut, tags=["auth"], summary="Register a new user")
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    - **email**: Must be unique. (valid email format)
    - **password**: Minimum 6 characters, stored as hash.
    Returns created user info (but not password).
    """
    existing = get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pwd = get_password_hash(user_in.password)
    user = User(email=user_in.email, password_hash=hashed_pwd)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/auth/login", response_model=Token, tags=["auth"], summary="User login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate with email and password and receive a JWT authorization token.

    Use OAuth2 form (field names: username, password).
    """
    # OAuth2PasswordRequestForm uses "username" for email by default!
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --- NOTES Endpoints (protected) ---

@app.post("/notes", response_model=NoteOut, tags=["notes"], summary="Create a new note", status_code=201)
def create_note(note: NoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Create a note for the authenticated user.
    """
    db_note = Note(
        title=note.title,
        content=note.content or "",
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@app.get("/notes", response_model=List[NoteOut], tags=["notes"], summary="Get all notes (mine)")
def list_notes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    List all notes belonging to the authenticated user,
    ordered by creation time descending.
    """
    return (
        db.query(Note)
        .filter(Note.owner_id == current_user.id)
        .order_by(Note.created_at.desc())
        .all()
    )

@app.get("/notes/{note_id}", response_model=NoteOut, tags=["notes"], summary="Get a specific note")
def get_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retrieve a specific note by ID, if owned by the user.
    """
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@app.patch("/notes/{note_id}", response_model=NoteOut, tags=["notes"], summary="Update a note")
def update_note(note_id: int, payload: NoteUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Update the title/content of a note. Only the owner may update it.
    Fields not passed are left unchanged.
    """
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    changed = False
    if payload.title is not None:
        note.title = payload.title
        changed = True
    if payload.content is not None:
        note.content = payload.content
        changed = True
    if changed:
        note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    return note

@app.delete("/notes/{note_id}", status_code=204, tags=["notes"], summary="Delete a note")
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Delete a specific note. Only allowed for the owner.
    """
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return

# --- Utility ---

@app.get("/auth/me", response_model=UserOut, tags=["auth"], summary="Get current user")
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the authenticated user's info.
    """
    return current_user

# ---- API USAGE EXAMPLES ----
#
# 1. Register user:
#    POST /auth/register { "email": "...", "password": "..." }
# 2. Login:
#    POST /auth/login (x-www-form-urlencoded: username, password) → { "access_token": ... }
# 3. Pass Authorization: Bearer <access_token> header for /notes endpoints.


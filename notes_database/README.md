# SecureNoteHub Notes Database

This folder defines database tables and setup for the SecureNoteHub application.

## Schema Overview

- **User**
  - `id` (int): Primary Key
  - `email` (str): Unique user email (authentication identity)
  - `password_hash` (str): Hashed password
  - `created_at` (datetime): Registration time

- **Note**
  - `id` (int): Primary Key
  - `title` (str): Note title
  - `content` (str): Note content (arbitrary text)
  - `owner_id` (int): User ID (foreign key)
  - `created_at` (datetime): Note creation time
  - `updated_at` (datetime): Last modification time

## Migrations

- `migrations/001_create_initial_tables.py`: Adds users and notes tables.
  - Run with: 
    ```
    python migrations/001_create_initial_tables.py
    ```
  - Requires environment variable `NOTES_DATABASE_URL` for DB URI (defaults to SQLite).

## Setup Script

- `setup_db.py`: (re)creates all tables using SQLAlchemy ORM metadata.
  - Run with:
    ```
    python setup_db.py
    ```
- Both scripts default to a local SQLite db (`notes_app.db`) if `NOTES_DATABASE_URL` is not set. Set this for production (e.g. PostgreSQL, MySQL).

## Usage

- Include/extend these models in the backend service for authentication & note CRUD.

# SecureNoteHub Notes Backend

This service provides the FastAPI backend for SecureNoteHub, enabling user authentication and CRUD operations on notes.

## Features

- **User Registration & Login:** Custom authentication system with hashed passwords and JWT tokens.
- **Notes CRUD:** Create, view, update, delete notes belonging to authenticated users.
- **RESTful API:** Ready for consumption by frontend (React) and REST tools.
- **CORS enabled:** Allows cross-origin requests (dev mode: all origins).

## Setup

1. **Set up the database (if not already done):**

   Use the `notes_database` setup script:

   ```
   cd ../notes_database
   python setup_db.py
   ```

2. **Configure environment variables:**

   - Copy `.env.example` to `.env` in this folder and edit as needed.
   - Ensure `NOTES_DATABASE_URL` points to your database (default works for local dev).

3. **Install dependencies:**

   ```
   pip install -r requirements.txt
   ```

4. **Run the API server:**

   ```
   cd src/api
   uvicorn main:app --reload
   ```

   Or from the backend container root:

   ```
   uvicorn src.api.main:app --reload
   ```

   The API will be served at [http://localhost:8000](http://localhost:8000).

## API Usage

*All endpoints except `/`, `/auth/register`, and `/auth/login` require a valid JWT as `Authorization: Bearer <token>` header.*

### Register

`POST /auth/register`
```json
{
  "email": "test@example.com",
  "password": "yourpassword"
}
```

### Login

`POST /auth/login` (use `application/x-www-form-urlencoded`, keys: `username`, `password`)
Returns:
```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

### Notes CRUD (Authenticated)

- **List Notes:**  
  `GET /notes`
- **Create Note:**  
  `POST /notes`  
  Body: `{ "title": "...", "content": "..." }`
- **Get by ID:**  
  `GET /notes/{note_id}`
- **Update:**  
  `PATCH /notes/{note_id}`  
  Body: `{ "title": "...?", "content": "...?" }`
- **Delete:**  
  `DELETE /notes/{note_id}`

Include the JWT token from `/auth/login` as a Bearer token for all `/notes` routes.

> See full OpenAPI docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

## Environment Variables

- `NOTES_DATABASE_URL`: SQLAlchemy DB URL (default: sqlite)
- `JWT_SECRET_KEY`: Secret for JWT signatures (change in production)
- `JWT_ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT token lifetime (default: 60)

## License

MIT


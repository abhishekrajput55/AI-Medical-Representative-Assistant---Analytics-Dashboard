# AI Medical Representative Assistant + Analytics Dashboard

## Status: Phase 1, Module 1 (Authentication) — complete

## What's built so far
- FastAPI backend scaffold with clean architecture (`models/ schemas/ routers/ core/`)
- PostgreSQL connection via SQLAlchemy
- User model with 5 roles (Admin, Product Manager, Regional Manager, Area Sales Manager, Medical Representative)
- JWT authentication: register, login, refresh, get current user (`/me`)
- Bcrypt password hashing
- Role-based access control (`require_role(...)` dependency, ready to use on future endpoints)
- Docker + docker-compose for one-command local setup

## How to run it

### Option A — Docker (easiest)
```bash
docker-compose up --build
```
Then open http://localhost:8000/docs — this is FastAPI's interactive Swagger UI.
You can register a user, log in, and try `/api/auth/me` directly from the browser.

### Option B — Manual
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env with real values
uvicorn app.main:app --reload
```
Requires a local PostgreSQL instance matching your `.env` DATABASE_URL.

## Try it out
1. `POST /api/auth/register` — create an account (pick a role)
2. `POST /api/auth/login` — get back an `access_token` and `refresh_token`
3. Click "Authorize" in `/docs`, paste the access token
4. `GET /api/auth/me` — confirms the token works and returns your profile

## Folder structure
```
medrep-ai/
├── backend/
│   ├── app/
│   │   ├── core/        # config, database, security, permission gates
│   │   ├── models/       # SQLAlchemy database tables
│   │   ├── schemas/      # Pydantic request/response shapes
│   │   ├── routers/       # API endpoints
│   │   ├── services/     # (next) business logic
│   │   ├── ai/            # (next) RAG chatbot
│   │   └── main.py       # app entrypoint
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/              # (next module)
└── docker-compose.yml
```

## Next module
**Doctor & Product Management** — the core data tables (Doctor, Chemist, Product)
plus CRUD APIs, protected by the auth we just built.

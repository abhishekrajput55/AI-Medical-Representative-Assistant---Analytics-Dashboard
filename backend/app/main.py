"""
Application entrypoint.

Run with:  uvicorn app.main:app --reload
Then open: http://localhost:8000/docs   (interactive Swagger API docs)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.routers import auth

# Import models so SQLAlchemy knows about every table before create_all().
from app.models import user  # noqa: F401

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered assistant and analytics platform for pharmaceutical sales teams.",
    version="0.1.0",
)

# CORS: without this, a browser blocks the React frontend (different
# origin/port) from calling this API at all — a built-in browser
# security rule. We explicitly allow our known frontend origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.on_event("startup")
def on_startup():
    # In real production you'd use Alembic migrations instead of
    # create_all(). We'll add Alembic in a later step — create_all()
    # is fine for getting Module 1 running and testable right now.
    Base.metadata.create_all(bind=engine)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}

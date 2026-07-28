"""
Centralized configuration.

Why bother? Because secrets (database passwords, JWT keys, API keys)
should NEVER be hard-coded into your Python files. If you hard-code
them and push to GitHub, anyone can steal them. Instead, we read
them from a `.env` file that is NEVER committed to version control.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "AI Medical Representative Assistant"
    ENV: str = "development"

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/medrep_ai"

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60          # short-lived login token
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7             # long-lived "stay logged in" token

    # --- AI ---
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # --- CORS: which frontend URLs are allowed to call this API ---
    FRONTEND_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

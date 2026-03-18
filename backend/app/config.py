"""Configuration management for RouteMind backend."""
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import field_validator
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/routemind"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 3600  # 1 hour default cache TTL

    # OpenAI
    # Set OPENAI_API_KEY in .env file or environment variable
    # For portfolio/demo: Set your key once at server level, users don't need their own
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # RAG / Embeddings
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    RAG_TOP_K: int = 50       # Number of semantic candidates to retrieve before optimization
    RAG_ENABLED: bool = False  # Set to True after running generate_embeddings.py

    # Google Places API
    GOOGLE_PLACES_API_KEY: Optional[str] = None  # Set in .env

    # CORS
    CORS_ORIGINS: list[str] | str = ["http://localhost:3000", "http://localhost:3001"]

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from JSON string or return list as-is."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # If not JSON, split by comma
                return [origin.strip() for origin in v.split(',')]
        return v

    # Session Management (no auth)
    SESSION_SECRET_KEY: str = "dev-secret-key-change-in-production"
    SESSION_COOKIE_NAME: str = "routemind_session"

    # JWT Authentication
    JWT_SECRET_KEY: str = "dev-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24 * 7  # 7 days

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    WS_MAX_CONNECTIONS_PER_SESSION: int = 5

    # Collaboration
    COLLAB_SESSION_TIMEOUT_MINUTES: int = 120  # 2 hours

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_HEAVY_ENDPOINTS: int = 10  # For expensive operations

    # Background Jobs (Celery)
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Logging & Monitoring
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None
    ENVIRONMENT: str = "development"  # development, staging, production

    # App
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    USE_ORTOOLS: bool = True  # Use OR-Tools optimizer (set to False to use greedy)

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


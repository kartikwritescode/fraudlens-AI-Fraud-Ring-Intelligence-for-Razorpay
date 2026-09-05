"""
Application Configuration Module
Powered by Pydantic v2 Settings.
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path

# Locate root .env if present
ROOT_DIR = Path(__file__).resolve().parents[4]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application
    APP_NAME: str = "FraudLens"
    APP_TITLE: str = "FraudLens — AI Fraud-Ring Intelligence for Razorpay"
    APP_TAGLINE: str = "See the fraud behind the transaction."
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    # PostgreSQL Configuration
    POSTGRES_USER: str = "fraudlens_admin"
    POSTGRES_PASSWORD: str = "fraudlens_secure_pass"
    POSTGRES_DB: str = "fraudlens"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://fraudlens_admin:fraudlens_secure_pass@localhost:5432/fraudlens"
    DATABASE_SYNC_URL: str = "postgresql://fraudlens_admin:fraudlens_secure_pass@localhost:5432/fraudlens"

    # Neo4j Graph Database Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "fraudlens_neo4j_pass"
    NEO4J_DATABASE: str = "neo4j"

    # Redis Cache / Message Broker (Phase 4)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Razorpay Test Configuration (Phase 5)
    RAZORPAY_KEY_ID: str = "rzp_test_placeholder"
    RAZORPAY_KEY_SECRET: str = "rzp_test_secret_placeholder"
    RAZORPAY_WEBHOOK_SECRET: str = "whsec_fraudlens_placeholder"


settings = Settings()

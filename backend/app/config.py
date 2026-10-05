import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    APP_ENV: str = Field(default="development")
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./kinetix.db")
    REDIS_URL: str = Field(default="")
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = Field(default="")
    GOOGLE_CLIENT_SECRET: str = Field(default="")
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:8000/api/auth/callback")
    TARGET_GMAIL_ACCOUNT: str = Field(default="exportdtp@gmail.com")
    
    # Google Drive / Sheets
    GOOGLE_DRIVE_FOLDER_ID: str = Field(default="")
    GOOGLE_SHEET_ID: str = Field(default="")
    
    # AI Provider
    AI_PROVIDER: str = Field(default="gemini")
    AI_API_KEY: str = Field(default="")
    
    # Security
    SESSION_SECRET: str = Field(default="kinetix-production-secret-key-32charsmin!")
    ENCRYPTION_KEY: str = Field(default="kinetix-token-encryption-secret-key32!")
    
    # Ingestion tuning
    BATCH_SIZE: int = Field(default=25)
    MAX_CONCURRENCY: int = Field(default=5)
    MAX_RETRIES: int = Field(default=3)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

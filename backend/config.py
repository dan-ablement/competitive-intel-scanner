import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/compintel"
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    ALLOWED_DOMAIN: str = "augmentcode.com"
    SESSION_SECRET: str = "change-me-in-production"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")


settings = Settings()


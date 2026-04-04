from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://dealradar:dealradar_dev@postgres:5432/dealradar"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "change-me-to-a-random-string"
    ENCRYPTION_KEY: str = "change-me-generate-a-real-fernet-key"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    BESTBUY_API_KEY: str = ""
    KEEPA_API_KEY: str = ""
    RAINFOREST_API_KEY: str = ""

    DISCORD_WEBHOOK_URL: str = ""
    SLACK_WEBHOOK_URL: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

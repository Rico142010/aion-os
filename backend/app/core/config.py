from datetime import datetime, timedelta, timezone

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AION OS"
    app_env: str = "development"
    api_prefix: str = "/api"

    postgres_db: str = "aion"
    postgres_user: str = "aion"
    postgres_password: str = "aion"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str = "postgresql+psycopg2://aion:aion@localhost:5432/aion"

    redis_host: str = "localhost"
    redis_port: int = 6379

    jwt_secret: str = "aion-super-secret-key-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24

    openai_api_key: str = ""
    default_admin_email: str = "admin@aion.io"
    default_admin_password: str = "admin123"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

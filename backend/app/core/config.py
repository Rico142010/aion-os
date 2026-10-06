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

    redis_host: str = "localhost"
    redis_port: int = 6379

    jwt_secret: str = "change-me"
    openai_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

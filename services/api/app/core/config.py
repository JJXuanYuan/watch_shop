from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = Field(default="watch-shop-api", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    secret_key: str = Field(default="change-me", alias="API_SECRET_KEY")
    database_url: str = Field(
        default="mysql+pymysql://watch_shop:watch_shop_123@mysql:3306/watch_shop",
        alias="DATABASE_URL",
    )
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")


@lru_cache
def get_settings() -> Settings:
    return Settings()

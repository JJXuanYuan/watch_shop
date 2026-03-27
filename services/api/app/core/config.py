from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


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
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="Admin@123456", alias="ADMIN_PASSWORD")
    admin_token_expire_minutes: int = Field(
        default=480,
        alias="ADMIN_TOKEN_EXPIRE_MINUTES",
    )
    user_token_secret: str = Field(default="change-user-token", alias="USER_TOKEN_SECRET")
    user_token_expire_minutes: int = Field(
        default=60 * 24 * 7,
        alias="USER_TOKEN_EXPIRE_MINUTES",
    )
    database_url: str = Field(
        default="mysql+pymysql://watch_shop:watch_shop_123@mysql:3306/watch_shop",
        alias="DATABASE_URL",
    )
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    media_root: str = Field(default="media", alias="MEDIA_ROOT")
    media_url_prefix: str = Field(default="/media", alias="MEDIA_URL_PREFIX")
    media_base_url: str | None = Field(default=None, alias="MEDIA_BASE_URL")
    media_image_max_bytes: int = Field(
        default=5 * 1024 * 1024,
        alias="MEDIA_IMAGE_MAX_BYTES",
    )
    wechat_mini_appid: str = Field(default="", alias="WECHAT_MINI_APPID")
    wechat_mini_secret: str = Field(default="", alias="WECHAT_MINI_SECRET")
    wechat_code2session_url: str = Field(
        default="https://api.weixin.qq.com/sns/jscode2session",
        alias="WECHAT_CODE2SESSION_URL",
    )
    wechat_login_timeout_seconds: int = Field(
        default=10,
        alias="WECHAT_LOGIN_TIMEOUT_SECONDS",
    )
    wechat_login_allow_dev_mock: bool = Field(
        default=True,
        alias="WECHAT_LOGIN_ALLOW_DEV_MOCK",
    )
    wechat_pay_mch_id: str = Field(default="", alias="WECHAT_PAY_MCH_ID")
    wechat_pay_merchant_serial_no: str = Field(
        default="",
        alias="WECHAT_PAY_MERCHANT_SERIAL_NO",
    )
    wechat_pay_private_key_path: str = Field(
        default="",
        alias="WECHAT_PAY_PRIVATE_KEY_PATH",
    )
    wechat_pay_platform_public_key_path: str = Field(
        default="",
        alias="WECHAT_PAY_PLATFORM_PUBLIC_KEY_PATH",
    )
    wechat_pay_platform_serial: str = Field(
        default="",
        alias="WECHAT_PAY_PLATFORM_SERIAL",
    )
    wechat_pay_api_v3_key: str = Field(default="", alias="WECHAT_PAY_API_V3_KEY")
    wechat_pay_notify_url: str = Field(default="", alias="WECHAT_PAY_NOTIFY_URL")
    wechat_pay_base_url: str = Field(
        default="https://api.mch.weixin.qq.com",
        alias="WECHAT_PAY_BASE_URL",
    )
    wechat_pay_timeout_seconds: int = Field(
        default=10,
        alias="WECHAT_PAY_TIMEOUT_SECONDS",
    )

    @property
    def resolved_media_root(self) -> Path:
        media_root = Path(self.media_root)
        if media_root.is_absolute():
            return media_root
        return BASE_DIR / media_root

    @property
    def normalized_media_url_prefix(self) -> str:
        prefix = self.media_url_prefix.strip() or "/media"
        if not prefix.startswith("/"):
            prefix = f"/{prefix}"
        return prefix.rstrip("/") or "/media"

    @property
    def resolved_media_base_url(self) -> str | None:
        if not self.media_base_url:
            return None
        return self.media_base_url.rstrip("/")

    @property
    def resolved_wechat_pay_private_key_path(self) -> Path | None:
        if not self.wechat_pay_private_key_path.strip():
            return None

        path = Path(self.wechat_pay_private_key_path)
        if path.is_absolute():
            return path
        return BASE_DIR / path

    @property
    def resolved_wechat_pay_platform_public_key_path(self) -> Path | None:
        if not self.wechat_pay_platform_public_key_path.strip():
            return None

        path = Path(self.wechat_pay_platform_public_key_path)
        if path.is_absolute():
            return path
        return BASE_DIR / path


@lru_cache
def get_settings() -> Settings:
    return Settings()

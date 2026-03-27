from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.types import UserStatus


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("username cannot be empty")
        return cleaned


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    username: str


class AdminProfileResponse(BaseModel):
    username: str


class WechatLoginRequest(BaseModel):
    code: str = Field(min_length=1, max_length=255)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("code cannot be empty")
        return cleaned


class UserProfileResponse(BaseModel):
    id: int
    nickname: str | None
    avatar_url: str | None
    status: UserStatus
    created_at: datetime
    updated_at: datetime


class WechatLoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserProfileResponse

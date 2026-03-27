from __future__ import annotations

import re

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def build_full_address(
    province: str,
    city: str,
    district: str,
    detail_address: str,
) -> str:
    return "".join(
        part.strip()
        for part in (province, city, district, detail_address)
        if part and part.strip()
    )


class AddressBaseRequest(BaseModel):
    receiver_name: str = Field(..., min_length=1, max_length=50)
    receiver_phone: str = Field(..., min_length=11, max_length=20)
    province: str = Field(..., min_length=1, max_length=50)
    city: str = Field(..., min_length=1, max_length=50)
    district: str = Field(..., min_length=1, max_length=50)
    detail_address: str = Field(..., min_length=1, max_length=255)
    is_default: bool = False

    @field_validator(
        "receiver_name",
        "province",
        "city",
        "district",
        "detail_address",
        mode="before",
    )
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("receiver_phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = value.strip()
        if not re.fullmatch(r"1\d{10}", normalized):
            raise ValueError("手机号格式不正确")
        return normalized


class AddressCreateRequest(AddressBaseRequest):
    pass


class AddressUpdateRequest(AddressBaseRequest):
    pass


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    receiver_name: str
    receiver_phone: str
    province: str
    city: str
    district: str
    detail_address: str
    full_address: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


class AddressListResponse(BaseModel):
    items: list[AddressResponse]


class AddressDefaultResponse(BaseModel):
    id: int
    is_default: bool

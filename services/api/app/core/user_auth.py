from __future__ import annotations

import base64
import binascii
import hmac
import json
import time
from dataclasses import dataclass
from hashlib import sha256

from app.core.config import get_settings

settings = get_settings()


class InvalidUserTokenError(ValueError):
    pass


@dataclass(frozen=True)
class UserIdentity:
    user_id: int


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _sign(payload_bytes: bytes) -> bytes:
    return hmac.new(
        settings.user_token_secret.encode("utf-8"),
        payload_bytes,
        sha256,
    ).digest()


def create_user_access_token(user_id: int) -> tuple[str, int]:
    expires_in = settings.user_token_expire_minutes * 60
    payload = {
        "sub": user_id,
        "role": "user",
        "exp": int(time.time()) + expires_in,
    }
    payload_bytes = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    signature = _sign(payload_bytes)
    token = f"{_b64encode(payload_bytes)}.{_b64encode(signature)}"
    return token, expires_in


def decode_user_access_token(token: str) -> UserIdentity:
    try:
        encoded_payload, encoded_signature = token.split(".", maxsplit=1)
        payload_bytes = _b64decode(encoded_payload)
        provided_signature = _b64decode(encoded_signature)
    except (ValueError, binascii.Error) as exc:
        raise InvalidUserTokenError("Invalid or expired user token") from exc

    expected_signature = _sign(payload_bytes)
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise InvalidUserTokenError("Invalid or expired user token")

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidUserTokenError("Invalid or expired user token") from exc

    if payload.get("role") != "user":
        raise InvalidUserTokenError("Invalid or expired user token")

    user_id = payload.get("sub")
    expires_at = payload.get("exp")
    if not isinstance(user_id, int) or user_id <= 0:
        raise InvalidUserTokenError("Invalid or expired user token")
    if not isinstance(expires_at, int) or expires_at <= int(time.time()):
        raise InvalidUserTokenError("Invalid or expired user token")

    return UserIdentity(user_id=user_id)

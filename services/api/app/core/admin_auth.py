from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from hashlib import sha256

from app.core.config import get_settings

settings = get_settings()

PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 390000
PASSWORD_SALT_BYTES = 16


class InvalidAdminTokenError(ValueError):
    pass


class InvalidPasswordHashError(ValueError):
    pass


@dataclass(frozen=True)
class AdminIdentity:
    admin_id: int
    username: str


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _sign(payload_bytes: bytes) -> bytes:
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        payload_bytes,
        sha256,
    ).digest()


def hash_admin_password(password: str) -> str:
    salt = secrets.token_hex(PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_HASH_ITERATIONS,
    )
    return (
        f"{PASSWORD_HASH_ALGORITHM}${PASSWORD_HASH_ITERATIONS}${salt}$"
        f"{digest.hex()}"
    )


def verify_admin_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt, expected_digest = password_hash.split(
            "$",
            maxsplit=3,
        )
        iterations = int(iterations_raw)
    except ValueError as exc:
        raise InvalidPasswordHashError("Invalid admin password hash") from exc

    if algorithm != PASSWORD_HASH_ALGORITHM or iterations <= 0:
        raise InvalidPasswordHashError("Invalid admin password hash")

    calculated_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return hmac.compare_digest(calculated_digest, expected_digest)


def create_admin_access_token(admin_id: int, username: str) -> tuple[str, int]:
    expires_in = settings.admin_token_expire_minutes * 60
    payload = {
        "sub": admin_id,
        "username": username,
        "role": "admin",
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


def decode_admin_access_token(token: str) -> AdminIdentity:
    try:
        encoded_payload, encoded_signature = token.split(".", maxsplit=1)
        payload_bytes = _b64decode(encoded_payload)
        provided_signature = _b64decode(encoded_signature)
    except (ValueError, binascii.Error) as exc:
        raise InvalidAdminTokenError("Invalid or expired admin token") from exc

    expected_signature = _sign(payload_bytes)
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise InvalidAdminTokenError("Invalid or expired admin token")

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidAdminTokenError("Invalid or expired admin token") from exc

    if payload.get("role") != "admin":
        raise InvalidAdminTokenError("Invalid or expired admin token")

    admin_id = payload.get("sub")
    username = payload.get("username")
    expires_at = payload.get("exp")
    if not isinstance(admin_id, int) or admin_id <= 0:
        raise InvalidAdminTokenError("Invalid or expired admin token")
    if not isinstance(username, str) or not username:
        raise InvalidAdminTokenError("Invalid or expired admin token")
    if not isinstance(expires_at, int) or expires_at <= int(time.time()):
        raise InvalidAdminTokenError("Invalid or expired admin token")

    return AdminIdentity(admin_id=admin_id, username=username)

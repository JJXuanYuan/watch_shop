from collections.abc import Generator

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.admin_auth import InvalidAdminTokenError, decode_admin_access_token
from app.core.user_auth import InvalidUserTokenError, decode_user_access_token
from app.db.session import SessionLocal
from app.models.admin_user import AdminUser
from app.models.types import AdminStatus, UserStatus
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_optional_anonymous_user_key(
    anonymous_user_key: str | None = Header(default=None, alias="X-Anonymous-User-Key"),
) -> str | None:
    cleaned = (anonymous_user_key or "").strip()
    if not cleaned:
        return None

    if len(cleaned) > 64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Anonymous-User-Key is too long",
        )

    return cleaned


def get_current_admin(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AdminUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        identity = decode_admin_access_token(credentials.credentials)
    except InvalidAdminTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    admin_user = db.get(AdminUser, identity.admin_id)
    if admin_user is None or admin_user.status != AdminStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return admin_user


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        identity = decode_user_access_token(credentials.credentials)
    except InvalidUserTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(User, identity.user_id)
    if user is None or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired user token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

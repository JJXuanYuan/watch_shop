from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.core.admin_auth import (
    InvalidPasswordHashError,
    create_admin_access_token,
    verify_admin_password,
)
from app.models.admin_user import AdminUser
from app.models.types import AdminStatus
from app.schemas.auth import AdminLoginRequest, AdminLoginResponse, AdminProfileResponse

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=AdminLoginResponse, summary="Admin login")
def admin_login(
    payload: AdminLoginRequest,
    db: Session = Depends(get_db),
) -> AdminLoginResponse:
    admin_user = db.scalar(
        select(AdminUser).where(AdminUser.username == payload.username.strip())
    )
    if admin_user is None or admin_user.status != AdminStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    try:
        is_valid_password = verify_admin_password(
            payload.password,
            admin_user.password_hash,
        )
    except InvalidPasswordHashError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin password configuration is invalid",
        ) from exc

    if not is_valid_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token, expires_in = create_admin_access_token(admin_user.id, admin_user.username)
    return AdminLoginResponse(
        access_token=access_token,
        expires_in=expires_in,
        username=admin_user.username,
    )


@router.get("/me", response_model=AdminProfileResponse, summary="Get current admin profile")
def get_admin_profile(
    current_admin: AdminUser = Depends(get_current_admin),
) -> AdminProfileResponse:
    return AdminProfileResponse(username=current_admin.username)

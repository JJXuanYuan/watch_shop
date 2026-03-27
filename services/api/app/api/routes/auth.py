from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_optional_anonymous_user_key
from app.core.user_auth import create_user_access_token
from app.core.users import merge_anonymous_user_data
from app.core.wechat import exchange_wechat_code
from app.models.types import UserStatus
from app.models.user import User
from app.schemas.auth import (
    UserProfileResponse,
    WechatLoginRequest,
    WechatLoginResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_user_profile(user: User) -> UserProfileResponse:
    return UserProfileResponse(
        id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/wechat-login", response_model=WechatLoginResponse, summary="Wechat mini program login")
def wechat_login(
    payload: WechatLoginRequest,
    anonymous_user_key: str | None = Depends(get_optional_anonymous_user_key),
    db: Session = Depends(get_db),
) -> WechatLoginResponse:
    session = exchange_wechat_code(payload.code)

    user = db.scalar(select(User).where(User.openid == session.openid))
    if user is None:
        user = User(
            openid=session.openid,
            unionid=session.unionid,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.flush()
    else:
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=403, detail="当前用户已被禁用")
        if session.unionid and user.unionid != session.unionid:
            user.unionid = session.unionid

    if anonymous_user_key:
        merge_anonymous_user_data(user, anonymous_user_key, db)

    db.commit()
    db.refresh(user)

    access_token, expires_in = create_user_access_token(user.id)
    return WechatLoginResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=_build_user_profile(user),
    )


@router.get("/me", response_model=UserProfileResponse, summary="Get current user profile")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    return _build_user_profile(current_user)

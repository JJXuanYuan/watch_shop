from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from fastapi import HTTPException, status

from app.core.config import get_settings

settings = get_settings()


@dataclass(frozen=True)
class WechatSession:
    openid: str
    unionid: str | None = None
    session_key: str | None = None


def _build_mock_openid(code: str) -> str:
    digest = hashlib.sha256(code.encode("utf-8")).hexdigest()[:28]
    return f"mock_openid_{digest}"


def exchange_wechat_code(code: str) -> WechatSession:
    normalized_code = code.strip()
    if not normalized_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信登录 code 不能为空",
        )

    if normalized_code.startswith("mock_"):
        if settings.app_env.lower() == "production" or not settings.wechat_login_allow_dev_mock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前环境不允许使用 mock 微信登录",
            )

        return WechatSession(openid=_build_mock_openid(normalized_code))

    if not settings.wechat_mini_appid or not settings.wechat_mini_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="微信小程序登录配置缺失",
        )

    query = urlencode(
        {
            "appid": settings.wechat_mini_appid,
            "secret": settings.wechat_mini_secret,
            "js_code": normalized_code,
            "grant_type": "authorization_code",
        }
    )
    request_url = f"{settings.wechat_code2session_url}?{query}"

    try:
        with urlopen(request_url, timeout=settings.wechat_login_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="调用微信登录服务失败",
        ) from exc

    errcode = payload.get("errcode")
    if errcode not in (None, 0):
        errmsg = payload.get("errmsg") or "微信登录失败"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"微信登录失败: {errmsg}",
        )

    openid = payload.get("openid")
    if not isinstance(openid, str) or not openid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信登录失败: 未获取到 openid",
        )

    unionid = payload.get("unionid")
    session_key = payload.get("session_key")

    return WechatSession(
        openid=openid,
        unionid=unionid if isinstance(unionid, str) and unionid else None,
        session_key=session_key if isinstance(session_key, str) and session_key else None,
    )

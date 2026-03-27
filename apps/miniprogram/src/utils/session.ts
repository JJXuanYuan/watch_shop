import { sendRequest } from "../api/client";
import type { UserProfile, WechatLoginResponse } from "../types/auth";

const ANONYMOUS_USER_KEY_STORAGE_KEY = "watch_shop_anonymous_user_key";
const USER_SESSION_STORAGE_KEY = "watch_shop_user_session";
const SESSION_EXPIRY_BUFFER_MS = 60 * 1000;

interface StoredUserSession {
  accessToken: string;
  expiresAt: number;
  user: UserProfile;
}

let loginPromise: Promise<StoredUserSession> | null = null;

function buildAnonymousUserKey(): string {
  return `guest_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}

function buildMockWechatCode(): string {
  return `mock_${getAnonymousUserKey()}`;
}

function isMockWechatLoginEnabled(): boolean {
  return (import.meta.env.VITE_WECHAT_LOGIN_MODE ?? "").toLowerCase() === "mock";
}

function parseStoredUserSession(value: unknown): StoredUserSession | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const payload = value as Partial<StoredUserSession>;
  if (
    typeof payload.accessToken !== "string" ||
    !payload.accessToken ||
    typeof payload.expiresAt !== "number" ||
    payload.expiresAt <= 0 ||
    !payload.user ||
    typeof payload.user.id !== "number"
  ) {
    return null;
  }

  return payload as StoredUserSession;
}

function getStoredUserSession(): StoredUserSession | null {
  return parseStoredUserSession(uni.getStorageSync(USER_SESSION_STORAGE_KEY));
}

function saveUserSession(payload: WechatLoginResponse): StoredUserSession {
  const storedSession: StoredUserSession = {
    accessToken: payload.access_token,
    expiresAt: Date.now() + payload.expires_in * 1000,
    user: payload.user,
  };
  uni.setStorageSync(USER_SESSION_STORAGE_KEY, storedSession);
  return storedSession;
}

function isStoredSessionValid(session: StoredUserSession | null): session is StoredUserSession {
  return Boolean(session && session.expiresAt - SESSION_EXPIRY_BUFFER_MS > Date.now());
}

function requestWechatCode(): Promise<string> {
  return new Promise((resolve, reject) => {
    uni.login({
      provider: "weixin",
      success: (result) => {
        if (typeof result.code === "string" && result.code.trim()) {
          resolve(result.code.trim());
          return;
        }

        if (isMockWechatLoginEnabled()) {
          resolve(buildMockWechatCode());
          return;
        }

        reject(new Error("未获取到有效的微信登录 code"));
      },
      fail: (error) => {
        if (isMockWechatLoginEnabled()) {
          resolve(buildMockWechatCode());
          return;
        }

        reject(new Error(error.errMsg || "微信登录失败"));
      },
    });
  });
}

async function performWechatLogin(): Promise<StoredUserSession> {
  const code = await requestWechatCode();
  const response = await sendRequest<WechatLoginResponse>({
    url: "/auth/wechat-login",
    method: "POST",
    data: { code },
    header: {
      "X-Anonymous-User-Key": getAnonymousUserKey(),
    },
  });

  return saveUserSession(response);
}

export function getAnonymousUserKey(): string {
  const cachedUserKey = uni.getStorageSync(ANONYMOUS_USER_KEY_STORAGE_KEY);
  if (typeof cachedUserKey === "string" && cachedUserKey.trim()) {
    return cachedUserKey;
  }

  const nextUserKey = buildAnonymousUserKey();
  uni.setStorageSync(ANONYMOUS_USER_KEY_STORAGE_KEY, nextUserKey);
  return nextUserKey;
}

export function getUserAccessToken(): string | null {
  const session = getStoredUserSession();
  if (!isStoredSessionValid(session)) {
    return null;
  }

  return session.accessToken;
}

export function getCurrentUserProfile(): UserProfile | null {
  const session = getStoredUserSession();
  return isStoredSessionValid(session) ? session.user : null;
}

export function clearUserSession(): void {
  uni.removeStorageSync(USER_SESSION_STORAGE_KEY);
}

export async function ensureUserSession(options: { forceRefresh?: boolean } = {}): Promise<StoredUserSession> {
  const shouldForceRefresh = options.forceRefresh === true;

  if (!shouldForceRefresh) {
    const cachedSession = getStoredUserSession();
    if (isStoredSessionValid(cachedSession)) {
      return cachedSession;
    }
  }

  clearUserSession();

  if (loginPromise) {
    return loginPromise;
  }

  loginPromise = performWechatLogin()
    .catch((error) => {
      clearUserSession();
      throw error;
    })
    .finally(() => {
      loginPromise = null;
    });

  return loginPromise;
}

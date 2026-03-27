import { ApiRequestError, sendRequest, type RawRequestOptions } from "./client";
import {
  clearUserSession,
  ensureUserSession,
  getAnonymousUserKey,
  getUserAccessToken,
} from "../utils/session";

interface RequestOptions extends RawRequestOptions {
  auth?: boolean;
  retryOnUnauthorized?: boolean;
}

function buildHeaders(header?: Record<string, string>): Record<string, string> {
  const accessToken = getUserAccessToken();

  return {
    "X-Anonymous-User-Key": getAnonymousUserKey(),
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    ...(header ?? {}),
  };
}

export async function request<T>({
  auth = false,
  retryOnUnauthorized = true,
  header,
  ...options
}: RequestOptions): Promise<T> {
  if (auth) {
    await ensureUserSession();
  }

  try {
    return await sendRequest<T>({
      ...options,
      header: buildHeaders(header),
    });
  } catch (error) {
    if (
      auth &&
      retryOnUnauthorized &&
      error instanceof ApiRequestError &&
      error.statusCode === 401
    ) {
      clearUserSession();
      await ensureUserSession({ forceRefresh: true });
      return request<T>({
        ...options,
        auth: true,
        header,
        retryOnUnauthorized: false,
      });
    }

    throw error;
  }
}

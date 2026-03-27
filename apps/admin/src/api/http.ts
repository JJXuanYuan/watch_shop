import { clearAdminSession, getAdminToken } from "../auth/session";

export class ApiError extends Error {
  statusCode: number;
  payload: unknown;

  constructor(message: string, statusCode: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.payload = payload;
  }
}

type RequestMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

interface RequestOptions {
  path: string;
  method?: RequestMethod;
  query?: Record<string, string | number | boolean | null | undefined>;
  body?: unknown;
  formData?: FormData;
  skipAuth?: boolean;
  handleUnauthorized?: boolean;
}

let unauthorizedHandler: (() => void) | null = null;

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1";

function getApiBaseUrl(): string {
  const rawBaseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
  return rawBaseUrl.replace(/\/$/, "");
}

function buildUrl(
  path: string,
  query?: Record<string, string | number | boolean | null | undefined>,
): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${getApiBaseUrl()}${normalizedPath}`);

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value === undefined || value === null || value === "") {
        return;
      }

      url.searchParams.set(key, String(value));
    });
  }

  return url.toString();
}

async function parseResponseBody(response: Response): Promise<unknown> {
  const rawText = await response.text();
  if (!rawText) {
    return undefined;
  }

  try {
    return JSON.parse(rawText) as unknown;
  } catch {
    return rawText;
  }
}

function resolveErrorMessage(response: Response, payload: unknown): string {
  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload &&
    typeof payload.detail === "string"
  ) {
    return payload.detail;
  }

  if (typeof payload === "string" && payload.trim()) {
    return payload;
  }

  return response.statusText || `Request failed with status ${response.status}`;
}

export function registerUnauthorizedHandler(handler: () => void): void {
  unauthorizedHandler = handler;
}

export async function request<T>({
  path,
  method = "GET",
  query,
  body,
  formData,
  skipAuth = false,
  handleUnauthorized = true,
}: RequestOptions): Promise<T> {
  const headers = new Headers();
  headers.set("Accept", "application/json");

  if (body !== undefined && formData !== undefined) {
    throw new Error("Request body and formData cannot be used together");
  }

  if (body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  if (!skipAuth) {
    const token = getAdminToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const response = await fetch(buildUrl(path, query), {
    method,
    headers,
    body:
      formData !== undefined
        ? formData
        : body === undefined
          ? undefined
          : JSON.stringify(body),
  });

  const payload = await parseResponseBody(response);

  if (!response.ok) {
    const error = new ApiError(
      resolveErrorMessage(response, payload),
      response.status,
      payload,
    );

    if (response.status === 401 && handleUnauthorized) {
      clearAdminSession();
      unauthorizedHandler?.();
    }

    throw error;
  }

  return payload as T;
}

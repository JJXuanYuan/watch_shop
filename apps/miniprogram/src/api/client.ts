type RequestMethod = NonNullable<UniApp.RequestOptions["method"]>;

export interface RawRequestOptions {
  url: string;
  method?: RequestMethod;
  data?: object | string | ArrayBuffer;
  header?: Record<string, string>;
}

interface ApiErrorPayload {
  detail?: string;
}

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1";

function resolveApiBaseUrl(): string {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
  return baseUrl.replace(/\/$/, "");
}

export class ApiRequestError extends Error {
  statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.name = "ApiRequestError";
    this.statusCode = statusCode;
  }
}

export const API_BASE_URL = resolveApiBaseUrl();

export function sendRequest<T>({
  url,
  method = "GET",
  data,
  header,
}: RawRequestOptions): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}${url}`,
      method: method as UniApp.RequestOptions["method"],
      data: data as UniApp.RequestOptions["data"],
      header: {
        Accept: "application/json",
        ...(header ?? {}),
      },
      success: (response) => {
        const statusCode = response.statusCode ?? 500;

        if (statusCode >= 200 && statusCode < 300) {
          resolve(response.data as T);
          return;
        }

        const payload = response.data as ApiErrorPayload | undefined;
        reject(
          new ApiRequestError(
            payload?.detail || `Request failed with ${statusCode}`,
            statusCode,
          ),
        );
      },
      fail: (error) => {
        reject(new Error(error.errMsg || "Network request failed"));
      },
    });
  });
}

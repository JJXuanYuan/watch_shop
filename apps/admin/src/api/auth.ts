import { request } from "./http";
import type { AdminLoginPayload, AdminLoginResponse, AdminProfileResponse } from "../types/admin";

export function loginAdmin(payload: AdminLoginPayload): Promise<AdminLoginResponse> {
  return request<AdminLoginResponse>({
    path: "/admin/auth/login",
    method: "POST",
    body: payload,
    skipAuth: true,
    handleUnauthorized: false,
  });
}

export function fetchAdminProfile(): Promise<AdminProfileResponse> {
  return request<AdminProfileResponse>({
    path: "/admin/auth/me",
    handleUnauthorized: false,
  });
}

import { request } from "./http";
import type {
  AdminCategoryItem,
  AdminCategoryListResponse,
  AdminCategoryPayload,
  CategoryStatusResponse,
} from "../types/admin";

export function fetchAdminCategories(): Promise<AdminCategoryListResponse> {
  return request<AdminCategoryListResponse>({
    path: "/admin/categories",
  });
}

export function createAdminCategory(payload: AdminCategoryPayload): Promise<AdminCategoryItem> {
  return request<AdminCategoryItem>({
    path: "/admin/categories",
    method: "POST",
    body: payload,
  });
}

export function updateAdminCategory(
  categoryId: number,
  payload: AdminCategoryPayload,
): Promise<AdminCategoryItem> {
  return request<AdminCategoryItem>({
    path: `/admin/categories/${categoryId}`,
    method: "PUT",
    body: payload,
  });
}

export function enableAdminCategory(categoryId: number): Promise<CategoryStatusResponse> {
  return request<CategoryStatusResponse>({
    path: `/admin/categories/${categoryId}/enable`,
    method: "PATCH",
  });
}

export function disableAdminCategory(categoryId: number): Promise<CategoryStatusResponse> {
  return request<CategoryStatusResponse>({
    path: `/admin/categories/${categoryId}/disable`,
    method: "PATCH",
  });
}

export function deleteAdminCategory(categoryId: number): Promise<void> {
  return request<void>({
    path: `/admin/categories/${categoryId}`,
    method: "DELETE",
  });
}

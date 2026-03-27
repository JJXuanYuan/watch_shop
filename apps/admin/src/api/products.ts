import { request } from "./http";
import type {
  AdminProductListResponse,
  AdminProductPayload,
  AdminProductResponse,
  ProductDeletedFilter,
  ProductDeletionResponse,
  ProductStatus,
  ProductStatusResponse,
} from "../types/admin";

interface ProductListParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  category_id?: number;
  status?: ProductStatus;
  deleted?: ProductDeletedFilter;
}

export function fetchAdminProducts(
  params: ProductListParams = {},
): Promise<AdminProductListResponse> {
  return request<AdminProductListResponse>({
    path: "/admin/products",
    query: params as Record<string, string | number | boolean | null | undefined>,
  });
}

export function fetchAdminProductDetail(productId: number): Promise<AdminProductResponse> {
  return request<AdminProductResponse>({
    path: `/admin/products/${productId}`,
  });
}

export function createAdminProduct(payload: AdminProductPayload): Promise<AdminProductResponse> {
  return request<AdminProductResponse>({
    path: "/admin/products",
    method: "POST",
    body: payload,
  });
}

export function updateAdminProduct(
  productId: number,
  payload: AdminProductPayload,
): Promise<AdminProductResponse> {
  return request<AdminProductResponse>({
    path: `/admin/products/${productId}`,
    method: "PUT",
    body: payload,
  });
}

export function putProductOnSale(productId: number): Promise<ProductStatusResponse> {
  return request<ProductStatusResponse>({
    path: `/admin/products/${productId}/on-sale`,
    method: "PATCH",
  });
}

export function takeProductOffSale(productId: number): Promise<ProductStatusResponse> {
  return request<ProductStatusResponse>({
    path: `/admin/products/${productId}/off-sale`,
    method: "PATCH",
  });
}

export function deleteAdminProduct(productId: number): Promise<void> {
  return request<void>({
    path: `/admin/products/${productId}`,
    method: "DELETE",
  });
}

export function restoreAdminProduct(productId: number): Promise<ProductDeletionResponse> {
  return request<ProductDeletionResponse>({
    path: `/admin/products/${productId}/restore`,
    method: "PATCH",
  });
}

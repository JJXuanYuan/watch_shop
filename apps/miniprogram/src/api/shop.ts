import { request } from "./http";
import type {
  CategoryListResponse,
  ProductDetail,
  ProductListResponse,
} from "../types/shop";

interface ProductListParams {
  category_id?: number;
  keyword?: string;
  page?: number;
  page_size?: number;
}

export function fetchCategories(): Promise<CategoryListResponse> {
  return request<CategoryListResponse>({
    url: "/categories",
  });
}

export function fetchProducts(
  params: ProductListParams = {},
): Promise<ProductListResponse> {
  return request<ProductListResponse>({
    url: "/products",
    data: params as Record<string, unknown>,
  });
}

export function fetchProductDetail(productId: number): Promise<ProductDetail> {
  return request<ProductDetail>({
    url: `/products/${productId}`,
  });
}

export type CategoryStatus = "enabled" | "disabled";
export type ProductStatus = "draft" | "on_sale" | "off_sale";
export type MoneyValue = number | string | null;

export interface CategoryItem {
  id: number;
  name: string;
  slug: string;
  sort_order: number;
  status: CategoryStatus;
}

export interface CategoryListResponse {
  items: CategoryItem[];
}

export interface ProductCategorySummary {
  id: number;
  name: string;
  slug: string;
  status: CategoryStatus;
}

export interface ProductListItem {
  id: number;
  category_id: number;
  category: ProductCategorySummary;
  name: string;
  title: string;
  subtitle: string | null;
  cover_image: string;
  price: MoneyValue;
  original_price: MoneyValue;
  stock: number;
  sales: number;
  status: ProductStatus;
  sort_order: number;
  is_featured: boolean;
  created_at: string;
}

export interface ProductListResponse {
  total: number;
  page: number;
  page_size: number;
  items: ProductListItem[];
}

export interface ProductDetail extends ProductListItem {
  banner_images: string[];
  image_list: string[];
  detail_content: string | null;
  detail: string | null;
  updated_at: string;
}

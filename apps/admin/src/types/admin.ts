export type ProductStatus = "draft" | "on_sale" | "off_sale";
export type CategoryStatus = "enabled" | "disabled";
export type ProductDeletedFilter = "not_deleted" | "deleted" | "all";
export type OrderStatus = "pending" | "paid" | "cancelled";
export type PaymentStatus = "unpaid" | "paid";
export type FulfillmentStatus = "unfulfilled" | "preparing" | "shipped" | "completed";
export type LogisticsCompanyStatus = "enabled" | "disabled";
export type MoneyValue = number | string | null;

export interface AdminLoginPayload {
  username: string;
  password: string;
}

export interface AdminLoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  username: string;
}

export interface AdminProfileResponse {
  username: string;
}

export interface AdminImageUploadResponse {
  url: string;
  filename: string;
  size: number;
  content_type: string;
}

export interface ProductCategorySummary {
  id: number;
  name: string;
  slug: string;
  status: CategoryStatus;
}

export interface AdminProductListItem {
  id: number;
  category_id: number;
  category: ProductCategorySummary;
  category_name: string;
  name: string;
  subtitle: string | null;
  price: MoneyValue;
  original_price: MoneyValue;
  stock: number;
  sales: number;
  status: ProductStatus;
  cover_image: string;
  sort_order: number;
  is_featured: boolean;
  deleted_at: string | null;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminProductResponse {
  id: number;
  category_id: number;
  category: ProductCategorySummary;
  name: string;
  subtitle: string | null;
  price: MoneyValue;
  original_price: MoneyValue;
  stock: number;
  sales: number;
  status: ProductStatus;
  cover_image: string;
  banner_images: string[];
  detail_content: string | null;
  sort_order: number;
  is_featured: boolean;
  deleted_at: string | null;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminProductListResponse {
  total: number;
  page: number;
  page_size: number;
  items: AdminProductListItem[];
}

export interface AdminProductPayload {
  name: string;
  subtitle: string | null;
  category_id: number;
  price: number;
  original_price: number | null;
  stock: number;
  sales: number;
  status: ProductStatus;
  cover_image: string;
  banner_images: string[];
  detail_content: string | null;
  sort_order: number;
  is_featured: boolean;
}

export interface ProductStatusResponse {
  id: number;
  status: ProductStatus;
}

export interface ProductDeletionResponse {
  id: number;
  deleted_at: string | null;
  is_deleted: boolean;
}

export interface AdminCategoryItem {
  id: number;
  name: string;
  slug: string;
  sort_order: number;
  status: CategoryStatus;
  product_count: number;
  created_at: string;
  updated_at: string;
}

export interface AdminCategoryListResponse {
  items: AdminCategoryItem[];
}

export interface AdminCategoryPayload {
  name: string;
  slug: string | null;
  sort_order: number;
}

export interface CategoryStatusResponse {
  id: number;
  status: CategoryStatus;
}

export interface OrderShippingInfo {
  shipping_company_code: string | null;
  shipping_company: string | null;
  tracking_no: string | null;
  shipping_note: string | null;
  shipped_at: string | null;
  completed_at: string | null;
}

export interface AdminOrderListItem extends OrderShippingInfo {
  id: number;
  order_no: string;
  payment_no: string;
  user_key: string;
  total_amount: MoneyValue;
  status: OrderStatus;
  payment_status: PaymentStatus;
  fulfillment_status: FulfillmentStatus;
  can_cancel: boolean;
  can_pay: boolean;
  item_count: number;
  total_quantity: number;
  paid_at: string | null;
  receiver_name: string | null;
  receiver_phone: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminOrderListResponse {
  total: number;
  page: number;
  page_size: number;
  items: AdminOrderListItem[];
}

export interface AdminOrderItem {
  id: number;
  product_id: number;
  product_name_snapshot: string;
  price_snapshot: MoneyValue;
  quantity: number;
  subtotal_amount: MoneyValue;
}

export interface OrderAddressSnapshot {
  receiver_name: string;
  receiver_phone: string;
  province: string;
  city: string;
  district: string;
  detail_address: string;
  full_address: string;
}

export interface AdminOrderResponse extends OrderShippingInfo {
  id: number;
  order_no: string;
  payment_no: string;
  user_key: string;
  total_amount: MoneyValue;
  status: OrderStatus;
  payment_status: PaymentStatus;
  fulfillment_status: FulfillmentStatus;
  can_cancel: boolean;
  can_pay: boolean;
  item_count: number;
  total_quantity: number;
  paid_at: string | null;
  transaction_id: string | null;
  address: OrderAddressSnapshot | null;
  created_at: string;
  updated_at: string;
  items: AdminOrderItem[];
}

export interface AdminOrderShipPayload {
  shipping_company_code?: string | null;
  shipping_company?: string | null;
  tracking_no: string;
  shipping_note?: string | null;
}

export interface LogisticsCompany {
  id: number;
  code: string;
  name: string;
  sort_order: number;
  status: LogisticsCompanyStatus;
  created_at: string;
  updated_at: string;
}

export interface LogisticsCompanyListResponse {
  items: LogisticsCompany[];
}

export interface AdminOrderOperationLog {
  log_id: number;
  order_id: number;
  admin_user_id: number | null;
  operator_username: string | null;
  action: string;
  action_label: string;
  before_status: OrderStatus | null;
  after_status: OrderStatus | null;
  before_fulfillment_status: FulfillmentStatus | null;
  after_fulfillment_status: FulfillmentStatus | null;
  detail: Record<string, unknown> | null;
  created_at: string;
}

export interface AdminOrderOperationLogListResponse {
  items: AdminOrderOperationLog[];
}

export interface OrderStatusResponse {
  id: number;
  status: OrderStatus;
  payment_status: PaymentStatus;
  fulfillment_status: FulfillmentStatus;
  can_cancel: boolean;
  can_pay: boolean;
}

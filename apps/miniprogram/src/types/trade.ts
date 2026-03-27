import type { MoneyValue, ProductStatus } from "./shop";

export type OrderStatus = "pending" | "paid" | "cancelled";
export type PaymentStatus = "unpaid" | "paid";
export type FulfillmentStatus = "unfulfilled" | "preparing" | "shipped" | "completed";
export type LogisticsCompanyStatus = "enabled" | "disabled";

export interface CartItem {
  id: number;
  product_id: number;
  name: string;
  subtitle: string | null;
  cover_image: string;
  price: MoneyValue;
  quantity: number;
  subtotal_amount: MoneyValue;
  stock: number;
  status: ProductStatus;
  is_available: boolean;
  availability_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface CartResponse {
  items: CartItem[];
  item_count: number;
  total_quantity: number;
  total_amount: MoneyValue;
}

export interface CartItemCreatePayload {
  product_id: number;
  quantity: number;
}

export interface CartItemUpdatePayload {
  quantity: number;
}

export interface OrderItem {
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

export interface OrderCreatePayload {
  address_id: number;
}

export interface OrderSummaryItem {
  id: number;
  product_id: number;
  product_name_snapshot: string;
  quantity: number;
}

export interface OrderShippingInfo {
  shipping_company_code: string | null;
  shipping_company: string | null;
  tracking_no: string | null;
  shipping_note: string | null;
  shipped_at: string | null;
  completed_at: string | null;
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

export interface OrderResponse extends OrderShippingInfo {
  id: number;
  order_no: string;
  payment_no: string;
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
  items: OrderItem[];
}

export interface OrderListItem extends OrderShippingInfo {
  id: number;
  order_no: string;
  payment_no: string;
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
  created_at: string;
  updated_at: string;
  items: OrderSummaryItem[];
}

export interface OrderListResponse {
  total: number;
  page: number;
  page_size: number;
  items: OrderListItem[];
}

export interface OrderStatusResponse {
  id: number;
  status: OrderStatus;
  payment_status: PaymentStatus;
  fulfillment_status: FulfillmentStatus;
  can_cancel: boolean;
  can_pay: boolean;
}

export interface OrderPaymentQueryResponse {
  synced: boolean;
  trade_state: string | null;
  trade_state_desc: string | null;
  order: OrderResponse;
}

export interface WechatPayCreateResponse {
  order_id: number;
  order_no: string;
  payment_no: string;
  appId: string;
  timeStamp: string;
  nonceStr: string;
  package: string;
  signType: string;
  paySign: string;
  prepayId: string;
}

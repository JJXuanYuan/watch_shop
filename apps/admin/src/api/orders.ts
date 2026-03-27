import { request } from "./http";
import type {
  AdminOrderListResponse,
  AdminOrderOperationLogListResponse,
  AdminOrderResponse,
  AdminOrderShipPayload,
  FulfillmentStatus,
  OrderStatus,
  PaymentStatus,
  OrderStatusResponse,
} from "../types/admin";

interface OrderListParams {
  page?: number;
  page_size?: number;
  order_no?: string;
  user_key?: string;
  status?: OrderStatus;
  payment_status?: PaymentStatus;
  fulfillment_status?: FulfillmentStatus;
}

export function fetchAdminOrders(
  params: OrderListParams = {},
): Promise<AdminOrderListResponse> {
  return request<AdminOrderListResponse>({
    path: "/admin/orders",
    query: params as Record<string, string | number | boolean | null | undefined>,
  });
}

export function fetchAdminOrderDetail(orderId: number): Promise<AdminOrderResponse> {
  return request<AdminOrderResponse>({
    path: `/admin/orders/${orderId}`,
  });
}

export function fetchAdminOrderLogs(
  orderId: number,
): Promise<AdminOrderOperationLogListResponse> {
  return request<AdminOrderOperationLogListResponse>({
    path: `/admin/orders/${orderId}/logs`,
  });
}

export function cancelAdminOrder(orderId: number): Promise<OrderStatusResponse> {
  return request<OrderStatusResponse>({
    path: `/admin/orders/${orderId}/cancel`,
    method: "PATCH",
  });
}

export function prepareAdminOrder(orderId: number): Promise<AdminOrderResponse> {
  return request<AdminOrderResponse>({
    path: `/admin/orders/${orderId}/prepare`,
    method: "PATCH",
  });
}

export function shipAdminOrder(
  orderId: number,
  body: AdminOrderShipPayload,
): Promise<AdminOrderResponse> {
  return request<AdminOrderResponse>({
    path: `/admin/orders/${orderId}/ship`,
    method: "PATCH",
    body,
  });
}

export function completeAdminOrder(orderId: number): Promise<AdminOrderResponse> {
  return request<AdminOrderResponse>({
    path: `/admin/orders/${orderId}/complete`,
    method: "PATCH",
  });
}

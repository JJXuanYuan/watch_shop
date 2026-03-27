import { request } from "./http";
import type {
  CartItemCreatePayload,
  CartItemUpdatePayload,
  CartResponse,
  OrderCreatePayload,
  OrderListResponse,
  OrderPaymentQueryResponse,
  OrderResponse,
  OrderStatusResponse,
  WechatPayCreateResponse,
} from "../types/trade";

export function fetchCart(): Promise<CartResponse> {
  return request<CartResponse>({
    url: "/cart",
    auth: true,
  });
}

export function addCartItem(payload: CartItemCreatePayload): Promise<CartResponse> {
  return request<CartResponse>({
    url: "/cart/items",
    method: "POST",
    data: payload,
    auth: true,
  });
}

export function updateCartItem(
  itemId: number,
  payload: CartItemUpdatePayload,
): Promise<CartResponse> {
  return request<CartResponse>({
    url: `/cart/items/${itemId}`,
    method: "PUT",
    data: payload,
    auth: true,
  });
}

export function deleteCartItem(itemId: number): Promise<void> {
  return request<void>({
    url: `/cart/items/${itemId}`,
    method: "DELETE",
    auth: true,
  });
}

export function createOrder(payload: OrderCreatePayload): Promise<OrderResponse> {
  return request<OrderResponse>({
    url: "/orders",
    method: "POST",
    data: payload,
    auth: true,
  });
}

export function fetchOrders(page = 1, pageSize = 20): Promise<OrderListResponse> {
  return request<OrderListResponse>({
    url: "/orders",
    data: {
      page,
      page_size: pageSize,
    },
    auth: true,
  });
}

export function fetchOrderDetail(orderId: number): Promise<OrderResponse> {
  return request<OrderResponse>({
    url: `/orders/${orderId}`,
    auth: true,
  });
}

export function createOrderPayment(orderId: number): Promise<WechatPayCreateResponse> {
  return request<WechatPayCreateResponse>({
    url: `/orders/${orderId}/pay`,
    method: "POST",
    auth: true,
  });
}

export function cancelOrder(orderId: number): Promise<OrderStatusResponse> {
  return request<OrderStatusResponse>({
    url: `/orders/${orderId}/cancel`,
    method: "POST",
    auth: true,
  });
}

export function queryOrderPayment(orderId: number): Promise<OrderPaymentQueryResponse> {
  return request<OrderPaymentQueryResponse>({
    url: `/orders/${orderId}/payment-query`,
    method: "POST",
    auth: true,
  });
}

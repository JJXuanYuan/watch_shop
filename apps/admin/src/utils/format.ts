import type {
  MoneyValue,
  ProductStatus,
  CategoryStatus,
  OrderStatus,
  PaymentStatus,
  FulfillmentStatus,
} from "../types/admin";

export function formatMoney(value: MoneyValue): string {
  if (value === null || value === undefined || value === "") {
    return "--";
  }

  const numericValue = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(numericValue)) {
    return "--";
  }

  return numericValue.toFixed(2);
}

export function formatDateTime(value: string): string {
  if (!value) {
    return "--";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function getProductStatusLabel(status: ProductStatus): string {
  switch (status) {
    case "draft":
      return "草稿";
    case "on_sale":
      return "上架中";
    case "off_sale":
      return "已下架";
    default:
      return status;
  }
}

export function getProductStatusTagType(status: ProductStatus): "" | "info" | "success" | "warning" {
  switch (status) {
    case "draft":
      return "info";
    case "on_sale":
      return "success";
    case "off_sale":
      return "warning";
    default:
      return "";
  }
}

export function getCategoryStatusLabel(status: CategoryStatus): string {
  return status === "enabled" ? "启用" : "禁用";
}

export function getCategoryStatusTagType(status: CategoryStatus): "" | "success" | "info" {
  return status === "enabled" ? "success" : "info";
}

export function getOrderStatusLabel(status: OrderStatus): string {
  switch (status) {
    case "pending":
      return "待支付";
    case "paid":
      return "已支付";
    case "cancelled":
      return "已取消";
    default:
      return status;
  }
}

export function getOrderStatusTagType(
  status: OrderStatus,
): "" | "warning" | "success" | "info" {
  switch (status) {
    case "pending":
      return "warning";
    case "paid":
      return "success";
    case "cancelled":
      return "info";
    default:
      return "";
  }
}

export function getPaymentStatusLabel(status: PaymentStatus): string {
  return status === "paid" ? "已支付" : "未支付";
}

export function getPaymentStatusTagType(status: PaymentStatus): "" | "success" | "info" {
  return status === "paid" ? "success" : "info";
}

export function getFulfillmentStatusLabel(status: FulfillmentStatus): string {
  switch (status) {
    case "preparing":
      return "备货中";
    case "shipped":
      return "已发货";
    case "completed":
      return "已完成";
    case "unfulfilled":
    default:
      return "待发货";
  }
}

export function getFulfillmentStatusTagType(
  status: FulfillmentStatus,
): "" | "warning" | "success" | "info" {
  switch (status) {
    case "preparing":
      return "warning";
    case "shipped":
      return "success";
    case "completed":
      return "success";
    case "unfulfilled":
    default:
      return "info";
  }
}

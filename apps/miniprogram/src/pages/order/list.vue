<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onPullDownRefresh, onShow } from "@dcloudio/uni-app";

import { fetchOrders } from "../../api/trade";
import { formatPrice } from "../../utils/price";
import { formatDateTime } from "../../utils/time";
import type {
  FulfillmentStatus,
  OrderListItem,
  OrderListResponse,
  OrderStatus,
} from "../../types/trade";

interface OrderListQuery {
  highlightOrderId?: string;
}

const orderList = ref<OrderListResponse | null>(null);
const loading = ref(false);
const errorMessage = ref("");
const highlightOrderId = ref<number | null>(null);

const visibleOrders = computed(() => orderList.value?.items ?? []);

function parseOrderId(value?: string): number | null {
  if (!value) {
    return null;
  }

  const numericValue = Number(value);
  return Number.isFinite(numericValue) && numericValue > 0 ? numericValue : null;
}

function buildOrderSummary(order: OrderListItem): string {
  if (!order.items.length) {
    return "暂无订单项";
  }

  const summary = order.items
    .slice(0, 2)
    .map((item) => `${item.product_name_snapshot} x${item.quantity}`)
    .join(" / ");

  if (order.items.length <= 2) {
    return summary;
  }

  return `${summary} 等 ${order.items.length} 件商品`;
}

function getOrderStatusLabel(status: OrderStatus): string {
  switch (status) {
    case "pending":
      return "待支付";
    case "cancelled":
      return "已取消";
    case "paid":
    default:
      return "已支付";
  }
}

function getFulfillmentLabel(status: FulfillmentStatus): string {
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

function getOrderStatusClass(status: OrderStatus): string {
  switch (status) {
    case "pending":
      return "status-chip--warning";
    case "cancelled":
      return "status-chip--muted";
    case "paid":
    default:
      return "status-chip--success";
  }
}

function getFulfillmentStatusClass(status: FulfillmentStatus): string {
  switch (status) {
    case "preparing":
      return "status-chip--warning";
    case "shipped":
    case "completed":
      return "status-chip--success";
    case "unfulfilled":
    default:
      return "status-chip--info";
  }
}

function getShippingCompanyDisplay(order: OrderListItem): string {
  if (order.shipping_company) {
    return order.shipping_company;
  }

  if (order.shipping_company_code) {
    return `物流公司 ${order.shipping_company_code}`;
  }

  return "物流公司";
}

function buildShippingSummary(order: OrderListItem): string {
  if (order.status === "paid" && order.fulfillment_status === "preparing") {
    return "商家正在备货，快递信息待录入";
  }

  if (order.status === "paid" && order.fulfillment_status === "unfulfilled") {
    return "订单已支付，等待商家发货";
  }

  if (
    order.status === "paid"
    && (order.fulfillment_status === "shipped" || order.fulfillment_status === "completed")
  ) {
    const company = getShippingCompanyDisplay(order);
    if (order.tracking_no) {
      const tail = order.tracking_no.slice(-4);
      return `${company} / 尾号 ${tail}`;
    }
    return `${company} / 单号待补充`;
  }

  if (order.receiver_name) {
    return `收货人：${order.receiver_name}`;
  }

  return "点击查看订单详情";
}

function buildActionHint(order: OrderListItem): string {
  if (order.can_pay) {
    return "可在详情页继续支付";
  }
  if (order.can_cancel) {
    return "可在详情页取消";
  }
  if (order.payment_status === "paid") {
    return "支付已完成";
  }
  return "查看订单详情";
}

async function loadOrders() {
  loading.value = true;
  errorMessage.value = "";

  try {
    orderList.value = await fetchOrders();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "订单列表加载失败";
    orderList.value = null;
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
}

function openCategoryPage() {
  uni.navigateTo({
    url: "/pages/category/index",
  });
}

function openOrderDetail(orderId: number) {
  uni.navigateTo({
    url: `/pages/order/detail?id=${orderId}`,
  });
}

onLoad((query) => {
  const pageQuery = (query ?? {}) as OrderListQuery;
  highlightOrderId.value = parseOrderId(pageQuery.highlightOrderId);
});

onShow(() => {
  void loadOrders();
});

onPullDownRefresh(() => {
  void loadOrders();
});
</script>

<template>
  <view class="page">
    <view class="header-card">
      <text class="header-kicker">Orders</text>
      <text class="header-title">我的订单</text>
      <text class="header-summary">
        这里会同步显示订单状态、支付状态和履约状态；已发货订单会和待发货、备货中订单明显区分。
      </text>
    </view>

    <view v-if="loading && !orderList" class="state-card">
      <text class="state-text">订单列表加载中...</text>
    </view>

    <view v-else-if="errorMessage && !orderList" class="state-card">
      <text class="state-title">订单列表加载失败</text>
      <text class="state-text">{{ errorMessage }}</text>
      <button class="state-button" size="mini" @tap="loadOrders">重新加载</button>
    </view>

    <view v-else-if="!visibleOrders.length" class="state-card">
      <text class="state-title">还没有订单</text>
      <text class="state-text">先去购物车提交一笔订单，这里会展示支付与人工发货状态的推进记录。</text>
      <button class="state-button" size="mini" @tap="openCategoryPage">去浏览商品</button>
    </view>

    <view v-else class="order-shell">
      <view
        v-for="order in visibleOrders"
        :key="order.id"
        class="order-card"
        :class="{ 'order-card--highlight': order.id === highlightOrderId }"
        @tap="openOrderDetail(order.id)"
      >
        <view class="order-head">
          <view class="order-head-main">
            <text class="order-no">{{ order.order_no }}</text>
            <text class="order-time">{{ formatDateTime(order.created_at) }}</text>
          </view>
          <view class="status-cluster">
            <text class="status-chip" :class="getOrderStatusClass(order.status)">
              {{ getOrderStatusLabel(order.status) }}
            </text>
            <text
              v-if="order.status === 'paid'"
              class="status-chip"
              :class="getFulfillmentStatusClass(order.fulfillment_status)"
            >
              {{ getFulfillmentLabel(order.fulfillment_status) }}
            </text>
          </view>
        </view>

        <text class="order-summary">{{ buildOrderSummary(order) }}</text>

        <view class="order-meta">
          <text class="order-meta-line">{{ buildShippingSummary(order) }}</text>
          <text class="order-meta-line">{{ buildActionHint(order) }}</text>
        </view>

        <view class="order-foot">
          <text class="order-count">共 {{ order.total_quantity }} 件商品</text>
          <text class="order-total">¥{{ formatPrice(order.total_amount) }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx;
  color: #2f2619;
}

.header-card,
.state-card,
.order-card {
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 18rpx 48rpx rgba(84, 62, 23, 0.08);
}

.header-card,
.state-card {
  padding: 30rpx 28rpx;
}

.header-kicker {
  display: block;
  color: #8d6c2f;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
  text-transform: uppercase;
}

.header-title {
  display: block;
  margin-top: 14rpx;
  font-size: 46rpx;
  font-weight: 700;
}

.header-summary,
.state-text {
  display: block;
  margin-top: 12rpx;
  color: #665946;
  font-size: 26rpx;
  line-height: 1.7;
}

.state-card,
.order-shell {
  margin-top: 24rpx;
}

.state-title {
  display: block;
  margin-bottom: 10rpx;
  font-size: 30rpx;
  font-weight: 700;
}

.state-button {
  margin-top: 18rpx;
  color: #20180d;
  background: #f0d59d;
}

.order-card + .order-card {
  margin-top: 18rpx;
}

.order-card {
  padding: 28rpx 26rpx;
}

.order-card--highlight {
  box-shadow: 0 24rpx 64rpx rgba(115, 85, 29, 0.18);
  border: 2rpx solid rgba(240, 213, 157, 0.72);
}

.order-head {
  display: flex;
  justify-content: space-between;
  gap: 18rpx;
}

.order-head-main {
  flex: 1;
  min-width: 0;
}

.order-no {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  line-height: 1.4;
  word-break: break-all;
}

.order-time {
  display: block;
  margin-top: 8rpx;
  color: #7c6d57;
  font-size: 24rpx;
}

.status-cluster {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10rpx;
}

.status-chip {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1.2;
}

.status-chip--warning {
  background: rgba(240, 213, 157, 0.46);
  color: #7d5d22;
}

.status-chip--success {
  background: rgba(186, 223, 177, 0.44);
  color: #2b6b2f;
}

.status-chip--muted {
  background: rgba(205, 197, 183, 0.5);
  color: #645846;
}

.status-chip--info {
  background: rgba(213, 222, 231, 0.52);
  color: #3f5f73;
}

.order-summary {
  display: block;
  margin-top: 18rpx;
  color: #564936;
  font-size: 26rpx;
  line-height: 1.7;
}

.order-meta {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-top: 18rpx;
}

.order-meta-line,
.order-count {
  color: #7c6d57;
  font-size: 24rpx;
  line-height: 1.6;
}

.order-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  margin-top: 20rpx;
}

.order-total {
  color: #20180d;
  font-size: 34rpx;
  font-weight: 700;
}
</style>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onPullDownRefresh } from "@dcloudio/uni-app";

import {
  cancelOrder,
  createOrderPayment,
  fetchOrderDetail,
  queryOrderPayment,
} from "../../api/trade";
import { formatPrice } from "../../utils/price";
import { formatDateTime } from "../../utils/time";
import type {
  FulfillmentStatus,
  OrderPaymentQueryResponse,
  OrderResponse,
  OrderStatus,
  WechatPayCreateResponse,
} from "../../types/trade";

interface OrderDetailQuery {
  id?: string;
}

const order = ref<OrderResponse | null>(null);
const orderId = ref<number | null>(null);
const loading = ref(false);
const cancelling = ref(false);
const paying = ref(false);
const confirmingPayment = ref(false);
const errorMessage = ref("");

const hasShippingInfo = computed(() => {
  if (!order.value) {
    return false;
  }

  return Boolean(
    order.value.shipping_company_code
    || order.value.shipping_company
    || order.value.tracking_no
    || order.value.shipped_at
    || order.value.completed_at
    || order.value.shipping_note,
  );
});

function parseOrderId(value?: string): number | null {
  if (!value) {
    return null;
  }

  const numericValue = Number(value);
  return Number.isFinite(numericValue) && numericValue > 0 ? numericValue : null;
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

function getPaymentStatusLabel(target: OrderResponse): string {
  return target.payment_status === "paid" ? "已支付" : "未支付";
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

function getFulfillmentDisplay(target: OrderResponse): string {
  if (target.status === "pending") {
    return "待支付后更新";
  }
  if (target.status === "cancelled") {
    return "--";
  }
  return getFulfillmentLabel(target.fulfillment_status);
}

function getOrderStatusClass(status: OrderStatus): string {
  switch (status) {
    case "pending":
      return "status-tag--warning";
    case "cancelled":
      return "status-tag--muted";
    case "paid":
    default:
      return "status-tag--success";
  }
}

function getFulfillmentStatusClass(target: OrderResponse): string {
  if (target.status === "pending") {
    return "status-tag--info";
  }
  if (target.status === "cancelled") {
    return "status-tag--muted";
  }

  switch (target.fulfillment_status) {
    case "preparing":
      return "status-tag--warning";
    case "shipped":
    case "completed":
      return "status-tag--success";
    case "unfulfilled":
    default:
      return "status-tag--info";
  }
}

function getShippingHint(target: OrderResponse): string {
  if (target.status === "pending") {
    return "支付成功后才会进入发货流程。";
  }
  if (target.status === "cancelled") {
    return "订单已取消，不再推进履约。";
  }
  if (target.fulfillment_status === "unfulfilled") {
    return "订单已支付，等待商家发货。";
  }
  if (target.fulfillment_status === "preparing") {
    return "订单正在备货中，快递信息待录入。";
  }
  return "商家已录入人工发货信息。";
}

function getShippingCompanyDisplay(target: OrderResponse): string {
  if (target.shipping_company) {
    return target.shipping_company;
  }

  if (target.shipping_company_code) {
    return `物流公司 ${target.shipping_company_code}`;
  }

  return "--";
}

function sleep(ms: number) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

async function loadOrderDetail() {
  if (!orderId.value) {
    errorMessage.value = "缺少订单 ID";
    order.value = null;
    uni.stopPullDownRefresh();
    return;
  }

  loading.value = true;
  errorMessage.value = "";

  try {
    order.value = await fetchOrderDetail(orderId.value);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "订单详情加载失败";
    order.value = null;
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
}

function backToOrderList() {
  uni.navigateBack({
    fail: () => {
      uni.navigateTo({
        url: "/pages/order/list",
      });
    },
  });
}

function requestWechatPayment(payload: WechatPayCreateResponse): Promise<void> {
  return new Promise((resolve, reject) => {
    uni.requestPayment({
      provider: "wxpay",
      timeStamp: payload.timeStamp,
      nonceStr: payload.nonceStr,
      package: payload.package,
      signType: payload.signType,
      paySign: payload.paySign,
      success: () => {
        resolve();
      },
      fail: (error) => {
        reject(error);
      },
    });
  });
}

function isPaymentCancelled(error: unknown): boolean {
  if (!error || typeof error !== "object") {
    return false;
  }

  const errMsg = "errMsg" in error ? String(error.errMsg || "") : "";
  return errMsg.toLowerCase().includes("cancel");
}

async function waitForPaidResult() {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    await loadOrderDetail();
    if (order.value?.status === "paid") {
      return true;
    }

    await sleep(1200);
  }

  return order.value?.status === "paid" ? true : false;
}

async function syncPaymentResult(silent = false): Promise<boolean> {
  if (!orderId.value || confirmingPayment.value) {
    return order.value?.status === "paid" ? true : false;
  }

  confirmingPayment.value = true;

  try {
    const result: OrderPaymentQueryResponse = await queryOrderPayment(orderId.value);
    order.value = result.order;

    if (!silent) {
      uni.showToast({
        title:
          result.order.status === "paid"
            ? "支付状态已同步"
            : result.trade_state_desc || "支付结果暂未确认",
        icon: result.order.status === "paid" ? "success" : "none",
      });
    }

    return result.order.status === "paid";
  } catch (error) {
    if (!silent) {
      uni.showToast({
        title: error instanceof Error ? error.message : "查单失败",
        icon: "none",
      });
    }
    return false;
  } finally {
    confirmingPayment.value = false;
  }
}

async function handlePayOrder() {
  if (!order.value?.can_pay || !orderId.value || paying.value) {
    return;
  }

  paying.value = true;

  try {
    const paymentPayload = await createOrderPayment(orderId.value);
    await requestWechatPayment(paymentPayload);

    let paidConfirmed = await waitForPaidResult();
    if (!paidConfirmed) {
      paidConfirmed = await syncPaymentResult(true);
    }

    uni.showToast({
      title: paidConfirmed ? "支付成功" : "支付结果确认中",
      icon: paidConfirmed ? "success" : "none",
    });
  } catch (error) {
    uni.showToast({
      title: isPaymentCancelled(error)
        ? "已取消支付"
        : error instanceof Error
          ? error.message
          : "支付失败，请稍后重试",
      icon: "none",
    });

    await loadOrderDetail();
  } finally {
    paying.value = false;
  }
}

function confirmCancelOrder() {
  if (!order.value?.can_cancel || cancelling.value) {
    return;
  }

  uni.showModal({
    title: "取消订单",
    content: "确认取消当前订单吗？取消后库存会回补，本阶段不支持恢复订单。",
    confirmColor: "#9a712d",
    success: async (result) => {
      if (!result.confirm || !orderId.value) {
        return;
      }

      cancelling.value = true;

      try {
        await cancelOrder(orderId.value);
        uni.showToast({
          title: "订单已取消",
          icon: "success",
        });
        await loadOrderDetail();
      } catch (error) {
        uni.showToast({
          title: error instanceof Error ? error.message : "取消订单失败",
          icon: "none",
        });
      } finally {
        cancelling.value = false;
      }
    },
  });
}

function copyTrackingNo() {
  if (!order.value?.tracking_no) {
    return;
  }

  uni.setClipboardData({
    data: order.value.tracking_no,
    success: () => {
      uni.showToast({
        title: "单号已复制",
        icon: "success",
      });
    },
  });
}

onLoad((query) => {
  const pageQuery = (query ?? {}) as OrderDetailQuery;
  orderId.value = parseOrderId(pageQuery.id);
  void loadOrderDetail();
});

onPullDownRefresh(() => {
  void loadOrderDetail();
});
</script>

<template>
  <view class="page">
    <view v-if="loading && !order" class="state-card">
      <text class="state-text">订单详情加载中...</text>
    </view>

    <view v-else-if="errorMessage && !order" class="state-card">
      <text class="state-title">订单详情加载失败</text>
      <text class="state-text">{{ errorMessage }}</text>
      <button class="state-button" size="mini" @tap="loadOrderDetail">重新加载</button>
    </view>

    <view v-else-if="order" class="detail-shell">
      <view class="overview-card">
        <text class="section-kicker">Order Detail</text>
        <text class="order-no">{{ order.order_no }}</text>
        <view class="overview-grid">
          <view class="overview-item">
            <text class="overview-label">订单状态</text>
            <text class="status-tag" :class="getOrderStatusClass(order.status)">
              {{ getOrderStatusLabel(order.status) }}
            </text>
          </view>
          <view class="overview-item">
            <text class="overview-label">支付状态</text>
            <text class="overview-value">{{ getPaymentStatusLabel(order) }}</text>
          </view>
          <view class="overview-item">
            <text class="overview-label">履约状态</text>
            <text class="status-tag" :class="getFulfillmentStatusClass(order)">
              {{ getFulfillmentDisplay(order) }}
            </text>
          </view>
          <view class="overview-item">
            <text class="overview-label">下单时间</text>
            <text class="overview-value">{{ formatDateTime(order.created_at) }}</text>
          </view>
          <view class="overview-item">
            <text class="overview-label">支付时间</text>
            <text class="overview-value">{{ order.paid_at ? formatDateTime(order.paid_at) : "--" }}</text>
          </view>
          <view class="overview-item">
            <text class="overview-label">订单金额</text>
            <text class="overview-value overview-value--strong">¥{{ formatPrice(order.total_amount) }}</text>
          </view>
          <view class="overview-item">
            <text class="overview-label">商品数量</text>
            <text class="overview-value">{{ order.total_quantity }} 件</text>
          </view>
        </view>
      </view>

      <view class="address-card">
        <text class="section-title">收货信息</text>
        <template v-if="order.address">
          <view class="address-meta">
            <text class="address-name">{{ order.address.receiver_name }}</text>
            <text class="address-phone">{{ order.address.receiver_phone }}</text>
          </view>
          <text class="address-text">{{ order.address.full_address }}</text>
        </template>
        <text v-else class="address-text">这笔历史订单还没有地址快照。</text>
      </view>

      <view class="shipping-card">
        <text class="section-title">发货信息</text>
        <template v-if="hasShippingInfo">
          <view class="shipping-row">
            <text class="shipping-label">快递公司</text>
            <text class="shipping-value">{{ getShippingCompanyDisplay(order) }}</text>
          </view>
          <view class="shipping-row">
            <text class="shipping-label">快递单号</text>
            <view class="shipping-value shipping-value--inline">
              <text>{{ order.tracking_no || "--" }}</text>
              <button
                v-if="order.tracking_no"
                class="copy-button"
                size="mini"
                @tap="copyTrackingNo"
              >
                复制单号
              </button>
            </view>
          </view>
          <view class="shipping-row">
            <text class="shipping-label">发货时间</text>
            <text class="shipping-value">{{ order.shipped_at ? formatDateTime(order.shipped_at) : "--" }}</text>
          </view>
          <view class="shipping-row">
            <text class="shipping-label">完成时间</text>
            <text class="shipping-value">{{ order.completed_at ? formatDateTime(order.completed_at) : "--" }}</text>
          </view>
          <view class="shipping-row">
            <text class="shipping-label">发货备注</text>
            <text class="shipping-value">{{ order.shipping_note || "--" }}</text>
          </view>
        </template>
        <text v-else class="shipping-hint">{{ getShippingHint(order) }}</text>
      </view>

      <view class="items-card">
        <text class="section-title">订单商品</text>

        <view
          v-for="item in order.items"
          :key="item.id"
          class="item-row"
        >
          <view class="item-head">
            <text class="item-name">{{ item.product_name_snapshot }}</text>
            <text class="item-subtotal">¥{{ formatPrice(item.subtotal_amount) }}</text>
          </view>
          <view class="item-foot">
            <text class="item-price">单价 ¥{{ formatPrice(item.price_snapshot) }}</text>
            <text class="item-quantity">数量 x{{ item.quantity }}</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="order" class="action-bar">
      <button class="secondary-button" @tap="backToOrderList">返回订单列表</button>
      <button
        v-if="order.can_pay"
        class="outline-button"
        :loading="confirmingPayment"
        @tap="syncPaymentResult()"
      >
        确认支付结果
      </button>
      <button
        v-if="order.can_pay"
        class="primary-button"
        :loading="paying"
        @tap="handlePayOrder"
      >
        立即支付
      </button>
      <button
        v-if="order.can_cancel"
        class="danger-button"
        :loading="cancelling"
        @tap="confirmCancelOrder"
      >
        取消订单
      </button>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx 24rpx 170rpx;
  color: #2f2619;
}

.detail-shell {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.overview-card,
.address-card,
.shipping-card,
.items-card,
.state-card {
  padding: 30rpx 28rpx;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 18rpx 48rpx rgba(84, 62, 23, 0.08);
}

.section-kicker {
  display: block;
  color: #8d6c2f;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
  text-transform: uppercase;
}

.section-title {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
}

.order-no {
  display: block;
  margin-top: 14rpx;
  font-size: 38rpx;
  font-weight: 700;
  line-height: 1.4;
  word-break: break-all;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
  margin-top: 22rpx;
}

.overview-item {
  padding: 22rpx 20rpx;
  border-radius: 24rpx;
  background: #fbf8f3;
}

.overview-label {
  display: block;
  color: #86775f;
  font-size: 22rpx;
}

.overview-value {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 1.5;
}

.overview-value--strong {
  font-size: 34rpx;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-top: 10rpx;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1.3;
}

.status-tag--warning {
  background: rgba(240, 213, 157, 0.46);
  color: #7d5d22;
}

.status-tag--success {
  background: rgba(186, 223, 177, 0.44);
  color: #2b6b2f;
}

.status-tag--muted {
  background: rgba(205, 197, 183, 0.5);
  color: #645846;
}

.status-tag--info {
  background: rgba(213, 222, 231, 0.52);
  color: #3f5f73;
}

.address-meta {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 18rpx;
}

.address-name,
.address-phone {
  font-size: 28rpx;
  font-weight: 700;
}

.address-text,
.shipping-hint {
  display: block;
  margin-top: 14rpx;
  color: #665946;
  font-size: 26rpx;
  line-height: 1.7;
}

.shipping-row + .shipping-row {
  margin-top: 18rpx;
}

.shipping-row {
  display: flex;
  justify-content: space-between;
  gap: 18rpx;
  margin-top: 18rpx;
}

.shipping-label {
  width: 140rpx;
  color: #86775f;
  font-size: 24rpx;
  line-height: 1.7;
}

.shipping-value {
  flex: 1;
  text-align: right;
  color: #2f2619;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.7;
  word-break: break-all;
}

.shipping-value--inline {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12rpx;
}

.copy-button {
  height: 58rpx;
  margin: 0;
  padding: 0 22rpx;
  border-radius: 999rpx;
  background: #2c2114;
  color: #fff7e8;
  font-size: 22rpx;
  line-height: 58rpx;
}

.items-card {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.item-row + .item-row {
  border-top: 1rpx solid rgba(141, 108, 47, 0.12);
  padding-top: 18rpx;
}

.item-head,
.item-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.item-name {
  flex: 1;
  font-size: 30rpx;
  font-weight: 700;
  line-height: 1.5;
}

.item-subtotal {
  color: #20180d;
  font-size: 30rpx;
  font-weight: 700;
}

.item-foot {
  margin-top: 12rpx;
}

.item-price,
.item-quantity,
.state-text {
  color: #6d604d;
  font-size: 26rpx;
  line-height: 1.7;
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

.action-bar {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  gap: 14rpx;
  padding: 18rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));
  background: rgba(250, 245, 236, 0.96);
  box-shadow: 0 -12rpx 30rpx rgba(62, 47, 19, 0.08);
}

.secondary-button,
.outline-button,
.primary-button,
.danger-button {
  flex: 1;
  height: 84rpx;
  margin: 0;
  border-radius: 999rpx;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 84rpx;
}

.secondary-button {
  border: none;
  background: #ead7b1;
  color: #20180d;
}

.outline-button {
  border: 2rpx solid rgba(44, 33, 20, 0.22);
  background: rgba(255, 255, 255, 0.88);
  color: #2c2114;
}

.primary-button {
  border: none;
  background: #2c2114;
  color: #fff7e8;
}

.danger-button {
  border: none;
  background: #7b3626;
  color: #fff7e8;
}

@media (max-width: 520px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .shipping-row {
    flex-direction: column;
  }

  .shipping-label,
  .shipping-value {
    width: auto;
    text-align: left;
  }

  .shipping-value--inline {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onPullDownRefresh, onShow } from "@dcloudio/uni-app";

import { deleteCartItem, fetchCart, updateCartItem } from "../../api/trade";
import { formatPrice } from "../../utils/price";
import type { CartResponse, CartItem } from "../../types/trade";

const cart = ref<CartResponse | null>(null);
const loading = ref(false);
const pendingItemId = ref<number | null>(null);
const deletingItemId = ref<number | null>(null);
const errorMessage = ref("");

const canCheckout = computed(() => {
  if (!cart.value || !cart.value.items.length) {
    return false;
  }

  return cart.value.items.every((item) => item.is_available);
});

const hasUnavailableItems = computed(() =>
  Boolean(cart.value?.items.some((item) => !item.is_available)),
);

async function loadCart() {
  loading.value = true;
  errorMessage.value = "";

  try {
    cart.value = await fetchCart();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "购物车加载失败";
    cart.value = null;
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

function openOrderListPage() {
  uni.navigateTo({
    url: "/pages/order/list",
  });
}

async function changeQuantity(item: CartItem, nextQuantity: number) {
  if (pendingItemId.value || nextQuantity <= 0) {
    return;
  }

  pendingItemId.value = item.id;

  try {
    cart.value = await updateCartItem(item.id, { quantity: nextQuantity });
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "修改数量失败",
      icon: "none",
    });
  } finally {
    pendingItemId.value = null;
  }
}

async function removeItem(item: CartItem) {
  if (deletingItemId.value) {
    return;
  }

  deletingItemId.value = item.id;

  try {
    await deleteCartItem(item.id);
    uni.showToast({
      title: "已移出购物车",
      icon: "success",
    });
    await loadCart();
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "删除失败",
      icon: "none",
    });
  } finally {
    deletingItemId.value = null;
  }
}

function goConfirmPage() {
  if (!canCheckout.value) {
    uni.showToast({
      title: hasUnavailableItems.value ? "请先处理不可下单商品" : "购物车为空",
      icon: "none",
    });
    return;
  }

  uni.navigateTo({
    url: "/pages/order/confirm",
  });
}

onShow(() => {
  void loadCart();
});

onPullDownRefresh(() => {
  void loadCart();
});
</script>

<template>
  <view class="page">
    <view class="header-card">
      <text class="header-kicker">Cart</text>
      <text class="header-title">购物车</text>
      <text class="header-summary">
        当前购物车已经绑定微信登录后的商城用户身份，重新进入页面会自动校验登录态。
      </text>
    </view>

    <view v-if="loading && !cart" class="state-card">
      <text class="state-text">购物车加载中...</text>
    </view>

    <view v-else-if="errorMessage && !cart" class="state-card">
      <text class="state-title">购物车加载失败</text>
      <text class="state-text">{{ errorMessage }}</text>
      <button class="state-button" size="mini" @tap="loadCart">重新加载</button>
    </view>

    <view v-else-if="!cart || !cart.items.length" class="state-card">
      <text class="state-title">购物车还是空的</text>
      <text class="state-text">先去商品详情页加购，再回来完成下单演示。</text>
      <view class="state-actions">
        <button class="secondary-button" size="mini" @tap="openCategoryPage">去逛逛</button>
        <button class="secondary-button" size="mini" @tap="openOrderListPage">查看订单</button>
      </view>
    </view>

    <view v-else class="cart-shell">
      <view
        v-if="hasUnavailableItems"
        class="warning-card"
      >
        <text class="warning-text">
          当前购物车中存在不可下单商品，请先删除或调整后再提交订单。
        </text>
      </view>

      <view
        v-for="item in cart.items"
        :key="item.id"
        class="cart-card"
      >
        <image :src="item.cover_image" class="cart-image" mode="aspectFill" />

        <view class="cart-content">
          <text class="cart-name">{{ item.name }}</text>
          <text v-if="item.subtitle" class="cart-subtitle">{{ item.subtitle }}</text>

          <view class="cart-meta-row">
            <text class="cart-price">¥{{ formatPrice(item.price) }}</text>
            <text class="cart-stock">库存 {{ item.stock }}</text>
          </view>

          <text
            v-if="!item.is_available"
            class="cart-warning"
          >
            {{ item.availability_message || "当前商品暂不可下单" }}
          </text>

          <view class="cart-footer">
            <view class="quantity-stepper">
              <button
                class="stepper-button"
                :disabled="pendingItemId === item.id || item.quantity <= 1"
                @tap="changeQuantity(item, item.quantity - 1)"
              >
                -
              </button>
              <text class="quantity-text">{{ item.quantity }}</text>
              <button
                class="stepper-button"
                :disabled="pendingItemId === item.id || !item.is_available || item.quantity >= item.stock"
                @tap="changeQuantity(item, item.quantity + 1)"
              >
                +
              </button>
            </view>

            <view class="cart-actions">
              <text class="cart-subtotal">小计 ¥{{ formatPrice(item.subtotal_amount) }}</text>
              <button
                class="delete-button"
                size="mini"
                :loading="deletingItemId === item.id"
                @tap="removeItem(item)"
              >
                删除
              </button>
            </view>
          </view>
        </view>
      </view>
    </view>

    <view v-if="cart && cart.items.length" class="action-bar">
      <view>
        <text class="summary-label">共 {{ cart.total_quantity }} 件商品</text>
        <text class="summary-total">¥{{ formatPrice(cart.total_amount) }}</text>
      </view>
      <button class="checkout-button" :disabled="!canCheckout" @tap="goConfirmPage">
        去结算
      </button>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx 24rpx 160rpx;
  color: #2f2619;
}

.header-card,
.state-card,
.warning-card,
.cart-card {
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 18rpx 48rpx rgba(84, 62, 23, 0.08);
}

.header-card {
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

.header-summary {
  display: block;
  margin-top: 12rpx;
  color: #665946;
  font-size: 26rpx;
  line-height: 1.7;
}

.state-card,
.warning-card {
  margin-top: 24rpx;
  padding: 32rpx 28rpx;
}

.state-title {
  display: block;
  margin-bottom: 10rpx;
  font-size: 30rpx;
  font-weight: 700;
}

.state-text,
.warning-text {
  color: #6d604d;
  font-size: 26rpx;
  line-height: 1.7;
}

.state-button,
.secondary-button {
  color: #20180d;
  background: #f0d59d;
}

.state-actions {
  display: flex;
  gap: 14rpx;
  margin-top: 18rpx;
}

.cart-shell {
  margin-top: 24rpx;
}

.cart-card + .cart-card {
  margin-top: 18rpx;
}

.cart-card {
  display: flex;
  overflow: hidden;
}

.cart-image {
  width: 220rpx;
  min-width: 220rpx;
  height: 220rpx;
  background: #efe4d2;
}

.cart-content {
  flex: 1;
  padding: 24rpx;
}

.cart-name {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  line-height: 1.45;
}

.cart-subtitle {
  display: block;
  margin-top: 10rpx;
  color: #6d604c;
  font-size: 24rpx;
  line-height: 1.6;
}

.cart-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16rpx;
}

.cart-price {
  color: #20180d;
  font-size: 34rpx;
  font-weight: 700;
}

.cart-stock {
  color: #8a7554;
  font-size: 24rpx;
}

.cart-warning {
  display: block;
  margin-top: 12rpx;
  color: #b65c32;
  font-size: 24rpx;
  line-height: 1.6;
}

.cart-footer {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-top: 20rpx;
  gap: 18rpx;
}

.quantity-stepper {
  display: inline-flex;
  align-items: center;
  padding: 8rpx;
  border-radius: 999rpx;
  background: #f7f1e7;
}

.stepper-button {
  width: 54rpx;
  height: 54rpx;
  padding: 0;
  border: none;
  border-radius: 999rpx;
  background: #ead7b1;
  color: #20180d;
  font-size: 34rpx;
  line-height: 54rpx;
}

.quantity-text {
  min-width: 48rpx;
  text-align: center;
  font-size: 28rpx;
  font-weight: 700;
}

.cart-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12rpx;
}

.cart-subtotal {
  color: #20180d;
  font-size: 28rpx;
  font-weight: 700;
}

.delete-button {
  margin: 0;
  color: #7f2f21;
  background: rgba(223, 183, 172, 0.42);
}

.action-bar {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));
  background: rgba(250, 245, 236, 0.96);
  box-shadow: 0 -12rpx 30rpx rgba(62, 47, 19, 0.08);
}

.summary-label {
  display: block;
  color: #6d604d;
  font-size: 22rpx;
}

.summary-total {
  display: block;
  margin-top: 8rpx;
  color: #20180d;
  font-size: 38rpx;
  font-weight: 700;
}

.checkout-button {
  min-width: 220rpx;
  height: 84rpx;
  margin: 0;
  border: none;
  border-radius: 999rpx;
  background: #2c2114;
  color: #fff7e8;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 84rpx;
}
</style>

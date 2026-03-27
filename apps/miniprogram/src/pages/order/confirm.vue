<script setup lang="ts">
import { computed, ref } from "vue";
import { onPullDownRefresh, onShow } from "@dcloudio/uni-app";

import { fetchAddresses } from "../../api/address";
import { fetchCart, createOrder } from "../../api/trade";
import { formatPrice } from "../../utils/price";
import type { UserAddress } from "../../types/address";
import type { CartResponse } from "../../types/trade";

const SELECTED_ADDRESS_STORAGE_KEY = "watch_shop_selected_address_id";

const cart = ref<CartResponse | null>(null);
const addresses = ref<UserAddress[]>([]);
const selectedAddressId = ref<number | null>(null);
const loading = ref(false);
const submitting = ref(false);
const errorMessage = ref("");

const selectedAddress = computed(() =>
  addresses.value.find((item) => item.id === selectedAddressId.value) ?? null,
);

const canSubmit = computed(() => {
  if (!cart.value || !cart.value.items.length || !selectedAddress.value) {
    return false;
  }

  return cart.value.items.every((item) => item.is_available);
});

function readStoredSelectedAddressId(): number | null {
  const value = uni.getStorageSync(SELECTED_ADDRESS_STORAGE_KEY);
  const numericValue = Number(value);
  return Number.isFinite(numericValue) && numericValue > 0 ? numericValue : null;
}

function persistSelectedAddressId(addressId: number | null) {
  if (addressId && addressId > 0) {
    uni.setStorageSync(SELECTED_ADDRESS_STORAGE_KEY, addressId);
    return;
  }

  uni.removeStorageSync(SELECTED_ADDRESS_STORAGE_KEY);
}

function syncSelectedAddress(nextAddresses: UserAddress[]) {
  if (!nextAddresses.length) {
    selectedAddressId.value = null;
    persistSelectedAddressId(null);
    return;
  }

  const storedId = readStoredSelectedAddressId();
  const matchedStoredAddress = nextAddresses.find((item) => item.id === storedId);
  if (matchedStoredAddress) {
    selectedAddressId.value = matchedStoredAddress.id;
    return;
  }

  const fallbackAddress =
    nextAddresses.find((item) => item.is_default) ??
    nextAddresses[0];
  selectedAddressId.value = fallbackAddress.id;
  persistSelectedAddressId(fallbackAddress.id);
}

async function loadPageData() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const [cartResponse, addressResponse] = await Promise.all([
      fetchCart(),
      fetchAddresses(),
    ]);
    cart.value = cartResponse;
    addresses.value = addressResponse.items;
    syncSelectedAddress(addressResponse.items);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "确认订单数据加载失败";
    cart.value = null;
    addresses.value = [];
    selectedAddressId.value = null;
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
}

function openCartPage() {
  uni.navigateBack({
    fail: () => {
      uni.navigateTo({
        url: "/pages/cart/index",
      });
    },
  });
}

function openAddressList() {
  const currentId = selectedAddress.value?.id;
  const suffix = currentId ? `&currentId=${currentId}` : "";
  uni.navigateTo({
    url: `/pages/address/index?select=1${suffix}`,
  });
}

function openAddressCreate() {
  uni.navigateTo({
    url: "/pages/address/form",
  });
}

async function handleSubmitOrder() {
  if (!canSubmit.value || submitting.value || !selectedAddress.value) {
    return;
  }

  submitting.value = true;

  try {
    const order = await createOrder({
      address_id: selectedAddress.value.id,
    });
    uni.showToast({
      title: "订单创建成功",
      icon: "success",
    });
    uni.redirectTo({
      url: `/pages/order/detail?id=${order.id}`,
    });
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "下单失败",
      icon: "none",
    });
  } finally {
    submitting.value = false;
  }
}

onShow(() => {
  void loadPageData();
});

onPullDownRefresh(() => {
  void loadPageData();
});
</script>

<template>
  <view class="page">
    <view class="header-card">
      <text class="header-kicker">Confirm</text>
      <text class="header-title">确认订单</text>
      <text class="header-summary">
        下单时会把当前选择的收货地址写入订单快照，后续修改地址簿不会影响历史订单展示。
      </text>
    </view>

    <view
      v-if="selectedAddress"
      class="address-card"
      @tap="openAddressList"
    >
      <view class="address-head">
        <text class="address-label">收货地址</text>
        <text class="address-link">更换地址</text>
      </view>
      <view class="address-meta">
        <text class="address-name">{{ selectedAddress.receiver_name }}</text>
        <text class="address-phone">{{ selectedAddress.receiver_phone }}</text>
        <text v-if="selectedAddress.is_default" class="address-tag">默认</text>
      </view>
      <text class="address-text">{{ selectedAddress.full_address }}</text>
    </view>

    <view v-else class="address-card address-card--empty">
      <text class="address-label">收货地址</text>
      <text class="address-title">还没有可用地址</text>
      <text class="address-text">请先新增一个真实收货地址，再提交订单。</text>
      <button class="state-button" size="mini" @tap="openAddressCreate">新增地址</button>
    </view>

    <view v-if="loading && !cart" class="state-card">
      <text class="state-text">待结算商品加载中...</text>
    </view>

    <view v-else-if="errorMessage && !cart" class="state-card">
      <text class="state-title">确认订单加载失败</text>
      <text class="state-text">{{ errorMessage }}</text>
      <button class="state-button" size="mini" @tap="loadPageData">重新加载</button>
    </view>

    <view v-else-if="!cart || !cart.items.length" class="state-card">
      <text class="state-title">暂无待结算商品</text>
      <text class="state-text">购物车为空时无法创建订单，请先去加购商品。</text>
      <button class="state-button" size="mini" @tap="openCartPage">返回购物车</button>
    </view>

    <view v-else class="order-shell">
      <view
        v-for="item in cart.items"
        :key="item.id"
        class="goods-card"
      >
        <image :src="item.cover_image" class="goods-image" mode="aspectFill" />
        <view class="goods-content">
          <text class="goods-name">{{ item.name }}</text>
          <text v-if="item.subtitle" class="goods-subtitle">{{ item.subtitle }}</text>
          <view class="goods-meta">
            <text class="goods-price">¥{{ formatPrice(item.price) }}</text>
            <text class="goods-count">x{{ item.quantity }}</text>
          </view>
          <text v-if="!item.is_available" class="goods-warning">
            {{ item.availability_message || "当前商品暂不可下单" }}
          </text>
        </view>
      </view>
    </view>

    <view v-if="cart && cart.items.length" class="action-bar">
      <view>
        <text class="summary-label">合计 {{ cart.total_quantity }} 件商品</text>
        <text class="summary-total">¥{{ formatPrice(cart.total_amount) }}</text>
      </view>
      <button
        class="submit-button"
        :disabled="!canSubmit || submitting"
        :loading="submitting"
        @tap="handleSubmitOrder"
      >
        提交订单
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
.address-card,
.goods-card,
.state-card {
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 18rpx 48rpx rgba(84, 62, 23, 0.08);
}

.header-card,
.address-card,
.state-card {
  padding: 30rpx 28rpx;
}

.header-kicker,
.address-label {
  display: block;
  color: #8d6c2f;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
  text-transform: uppercase;
}

.header-title,
.address-title {
  display: block;
  margin-top: 14rpx;
  font-size: 40rpx;
  font-weight: 700;
}

.header-summary,
.address-text,
.state-text {
  display: block;
  margin-top: 12rpx;
  color: #665946;
  font-size: 26rpx;
  line-height: 1.7;
}

.address-card,
.state-card,
.order-shell {
  margin-top: 24rpx;
}

.address-card--empty {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.address-head,
.address-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.address-head {
  width: 100%;
}

.address-link {
  color: #9a712d;
  font-size: 24rpx;
  font-weight: 700;
}

.address-meta {
  justify-content: flex-start;
  margin-top: 16rpx;
}

.address-name,
.address-phone {
  font-size: 30rpx;
  font-weight: 700;
}

.address-tag {
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(240, 213, 157, 0.4);
  color: #8d6c2f;
  font-size: 22rpx;
  font-weight: 700;
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

.goods-card + .goods-card {
  margin-top: 18rpx;
}

.goods-card {
  display: flex;
  overflow: hidden;
}

.goods-image {
  width: 220rpx;
  min-width: 220rpx;
  height: 220rpx;
  background: #efe4d2;
}

.goods-content {
  flex: 1;
  padding: 24rpx;
}

.goods-name {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  line-height: 1.45;
}

.goods-subtitle {
  display: block;
  margin-top: 10rpx;
  color: #6d604c;
  font-size: 24rpx;
  line-height: 1.6;
}

.goods-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 18rpx;
}

.goods-price {
  color: #20180d;
  font-size: 34rpx;
  font-weight: 700;
}

.goods-count {
  color: #8a7554;
  font-size: 24rpx;
}

.goods-warning {
  display: block;
  margin-top: 12rpx;
  color: #b65c32;
  font-size: 24rpx;
  line-height: 1.6;
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

.submit-button {
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

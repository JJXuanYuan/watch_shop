<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onPullDownRefresh, onShow } from "@dcloudio/uni-app";

import { deleteAddress, fetchAddresses, setDefaultAddress } from "../../api/address";
import type { AddressListResponse, UserAddress } from "../../types/address";

const SELECTED_ADDRESS_STORAGE_KEY = "watch_shop_selected_address_id";

interface AddressPageQuery {
  select?: string;
  currentId?: string;
}

const loading = ref(false);
const deletingId = ref<number | null>(null);
const defaultingId = ref<number | null>(null);
const addresses = ref<UserAddress[]>([]);
const errorMessage = ref("");
const selectMode = ref(false);
const currentId = ref<number | null>(null);

const pageTitle = computed(() => (selectMode.value ? "选择收货地址" : "地址管理"));

function parseNumber(value?: string): number | null {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) && numericValue > 0 ? numericValue : null;
}

async function loadAddresses() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const response: AddressListResponse = await fetchAddresses();
    addresses.value = response.items;
    if (selectMode.value) {
      currentId.value = parseNumber(String(uni.getStorageSync(SELECTED_ADDRESS_STORAGE_KEY))) ?? currentId.value;
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "地址加载失败";
    addresses.value = [];
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
}

function openCreateForm() {
  uni.navigateTo({
    url: "/pages/address/form",
  });
}

function openEditForm(addressId: number) {
  uni.navigateTo({
    url: `/pages/address/form?id=${addressId}`,
  });
}

function chooseAddress(address: UserAddress) {
  if (!selectMode.value) {
    return;
  }

  uni.setStorageSync(SELECTED_ADDRESS_STORAGE_KEY, address.id);
  uni.navigateBack();
}

async function handleSetDefault(address: UserAddress) {
  if (address.is_default || defaultingId.value) {
    return;
  }

  defaultingId.value = address.id;

  try {
    await setDefaultAddress(address.id);
    uni.showToast({
      title: "默认地址已更新",
      icon: "success",
    });
    await loadAddresses();
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "设置默认失败",
      icon: "none",
    });
  } finally {
    defaultingId.value = null;
  }
}

function confirmDelete(address: UserAddress) {
  if (deletingId.value) {
    return;
  }

  uni.showModal({
    title: "删除地址",
    content: `确认删除“${address.receiver_name} ${address.receiver_phone}”这条地址吗？`,
    confirmColor: "#9a712d",
    success: async (result) => {
      if (!result.confirm) {
        return;
      }

      deletingId.value = address.id;

      try {
        await deleteAddress(address.id);
        if (currentId.value === address.id) {
          uni.removeStorageSync(SELECTED_ADDRESS_STORAGE_KEY);
        }
        uni.showToast({
          title: "地址已删除",
          icon: "success",
        });
        await loadAddresses();
      } catch (error) {
        uni.showToast({
          title: error instanceof Error ? error.message : "删除地址失败",
          icon: "none",
        });
      } finally {
        deletingId.value = null;
      }
    },
  });
}

onLoad((query) => {
  const pageQuery = (query ?? {}) as AddressPageQuery;
  selectMode.value = pageQuery.select === "1";
  currentId.value = parseNumber(pageQuery.currentId);
  uni.setNavigationBarTitle({
    title: pageTitle.value,
  });
});

onShow(() => {
  void loadAddresses();
});

onPullDownRefresh(() => {
  void loadAddresses();
});
</script>

<template>
  <view class="page">
    <view class="header-card">
      <text class="header-kicker">Address</text>
      <text class="header-title">{{ pageTitle }}</text>
      <text class="header-summary">
        地址属于当前微信登录用户；下单时会把所选地址写入订单快照，后续可独立维护地址簿。
      </text>
    </view>

    <view v-if="loading && !addresses.length" class="state-card">
      <text class="state-text">地址列表加载中...</text>
    </view>

    <view v-else-if="errorMessage && !addresses.length" class="state-card">
      <text class="state-title">地址列表加载失败</text>
      <text class="state-text">{{ errorMessage }}</text>
      <button class="state-button" size="mini" @tap="loadAddresses">重新加载</button>
    </view>

    <view v-else-if="!addresses.length" class="state-card">
      <text class="state-title">还没有地址</text>
      <text class="state-text">先新增一个常用收货地址，确认订单时就能直接带出。</text>
      <button class="state-button" size="mini" @tap="openCreateForm">新增地址</button>
    </view>

    <view v-else class="address-shell">
      <view
        v-for="address in addresses"
        :key="address.id"
        class="address-card"
        :class="{ 'address-card--current': address.id === currentId }"
        @tap="chooseAddress(address)"
      >
        <view class="address-head">
          <view class="address-meta">
            <text class="address-name">{{ address.receiver_name }}</text>
            <text class="address-phone">{{ address.receiver_phone }}</text>
          </view>
          <view class="address-tags">
            <text v-if="address.is_default" class="address-tag">默认</text>
            <text
              v-if="selectMode && address.id === currentId"
              class="address-tag address-tag--current"
            >
              当前
            </text>
          </view>
        </view>

        <text class="address-text">{{ address.full_address }}</text>

        <view class="address-actions">
          <button
            class="mini-button"
            size="mini"
            :disabled="address.is_default"
            :loading="defaultingId === address.id"
            @tap.stop="handleSetDefault(address)"
          >
            设为默认
          </button>
          <button class="mini-button" size="mini" @tap.stop="openEditForm(address.id)">编辑</button>
          <button
            class="mini-button mini-button--danger"
            size="mini"
            :loading="deletingId === address.id"
            @tap.stop="confirmDelete(address)"
          >
            删除
          </button>
        </view>
      </view>
    </view>

    <view class="footer-action">
      <button class="create-button" @tap="openCreateForm">新增地址</button>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx 24rpx 48rpx;
  color: #2f2619;
}

.header-card,
.state-card,
.address-card {
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18rpx 48rpx rgba(84, 62, 23, 0.08);
}

.header-card,
.state-card,
.address-card {
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
  font-size: 42rpx;
  font-weight: 700;
}

.header-summary,
.state-text,
.address-text {
  display: block;
  margin-top: 12rpx;
  color: #665946;
  font-size: 26rpx;
  line-height: 1.7;
}

.state-card,
.address-shell,
.footer-action {
  margin-top: 24rpx;
}

.state-title {
  display: block;
  margin-bottom: 10rpx;
  font-size: 30rpx;
  font-weight: 700;
}

.state-button,
.mini-button,
.create-button {
  color: #20180d;
  background: #f0d59d;
}

.address-card + .address-card {
  margin-top: 18rpx;
}

.address-card--current {
  border: 2rpx solid rgba(154, 113, 45, 0.28);
}

.address-head,
.address-meta,
.address-tags,
.address-actions {
  display: flex;
  align-items: center;
}

.address-head {
  justify-content: space-between;
  gap: 18rpx;
}

.address-meta,
.address-tags,
.address-actions {
  gap: 12rpx;
}

.address-name,
.address-phone {
  font-size: 30rpx;
  font-weight: 700;
}

.address-tag {
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(240, 213, 157, 0.42);
  color: #8d6c2f;
  font-size: 22rpx;
  font-weight: 700;
}

.address-tag--current {
  background: rgba(44, 33, 20, 0.12);
  color: #2c2114;
}

.address-actions {
  margin-top: 18rpx;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.mini-button {
  margin: 0;
}

.mini-button--danger {
  color: #7b3626;
  background: rgba(223, 183, 172, 0.42);
}

.create-button {
  height: 84rpx;
  border: none;
  border-radius: 999rpx;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 84rpx;
}
</style>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onPullDownRefresh, onShow } from "@dcloudio/uni-app";

import TechTabBar from "../../components/TechTabBar.vue";
import { fetchOrders } from "../../api/trade";
import { getFavoriteProducts } from "../../utils/favorites";
import {
  ensureUserSession,
  getCurrentUserProfile,
} from "../../utils/session";
import { formatDateTime } from "../../utils/time";
import type { UserProfile } from "../../types/auth";
import type { OrderListItem } from "../../types/trade";

const user = ref<UserProfile | null>(getCurrentUserProfile());
const orders = ref<OrderListItem[]>([]);
const loading = ref(false);

const favoriteProducts = ref(getFavoriteProducts());
const pendingPayCount = computed(() =>
  orders.value.filter((item) => item.status === "pending").length,
);
const toShipCount = computed(() =>
  orders.value.filter((item) => (
    item.status === "paid"
    && (item.fulfillment_status === "unfulfilled" || item.fulfillment_status === "preparing")
  )).length,
);
const toReceiveCount = computed(() =>
  orders.value.filter((item) => item.fulfillment_status === "shipped").length,
);
const profileName = computed(() =>
  user.value?.nickname?.trim() || `微信用户 ${user.value?.id ?? ""}`.trim(),
);
const memberSince = computed(() => {
  if (!user.value?.created_at) {
    return "会员资格已开通";
  }

  return `注册于 ${formatDateTime(user.value.created_at)}`;
});

const actionCards = computed(() => [
  {
    key: "pending",
    label: "待付款",
    value: pendingPayCount.value,
    subtitle: "待支付订单",
  },
  {
    key: "shipping",
    label: "待发货",
    value: toShipCount.value,
    subtitle: "商家处理中",
  },
  {
    key: "receiving",
    label: "待收货",
    value: toReceiveCount.value,
    subtitle: "物流途中",
  },
  {
    key: "favorite",
    label: "我的收藏",
    value: favoriteProducts.value.length,
    subtitle: "本地已收藏商品",
  },
]);

async function loadMyPageData() {
  loading.value = true;

  try {
    const session = await ensureUserSession();
    user.value = session.user;
  } catch {
    user.value = getCurrentUserProfile();
  }

  favoriteProducts.value = getFavoriteProducts();

  try {
    const response = await fetchOrders();
    orders.value = response.items;
  } catch {
    orders.value = [];
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
}

function openOrderListPage() {
  uni.navigateTo({
    url: "/pages/order/list",
  });
}

function handleActionTap(actionKey: string) {
  if (actionKey === "favorite") {
    const favorite = favoriteProducts.value[0];
    if (!favorite) {
      uni.showToast({
        title: "当前还没有收藏商品",
        icon: "none",
      });
      return;
    }

    uni.navigateTo({
      url: `/pages/product/detail?id=${favorite.id}`,
    });
    return;
  }

  openOrderListPage();
}

onShow(() => {
  void loadMyPageData();
});

onPullDownRefresh(() => {
  void loadMyPageData();
});
</script>

<template>
  <view class="tech-page my-page">
    <view class="tech-shell">
      <view class="tech-nav my-nav tech-fade-up">
        <view class="tech-nav__side"></view>

        <view class="tech-nav__center">
          <text class="tech-nav__title">我的</text>
          <text class="tech-nav__subtitle">VIP PROFILE</text>
        </view>

        <button
          class="tech-icon-button"
          hover-class="tech-button-hover"
          @tap="openOrderListPage"
        >
          订单
        </button>
      </view>

      <view class="tech-panel tech-panel-pad my-vip tech-fade-scale tech-delay-1">
        <view class="my-vip__head">
          <view class="my-vip__avatar">VIP</view>

          <view class="my-vip__copy">
            <text class="tech-kicker">尊享会员</text>
            <text class="my-vip__title">{{ profileName }}</text>
            <text class="my-vip__summary">{{ memberSince }}</text>
          </view>
        </view>

        <view class="my-vip__signals">
          <view class="my-vip__signal">
            <text class="my-vip__signal-label">订单</text>
            <text class="my-vip__signal-value">{{ orders.length }}</text>
          </view>
          <view class="my-vip__signal">
            <text class="my-vip__signal-label">收藏</text>
            <text class="my-vip__signal-value">{{ favoriteProducts.length }}</text>
          </view>
          <view class="my-vip__signal">
            <text class="my-vip__signal-label">状态</text>
            <text class="my-vip__signal-value">{{ user?.status === "active" ? "正常" : "待同步" }}</text>
          </view>
        </view>
      </view>

      <view class="my-actions">
        <view
          v-for="(action, index) in actionCards"
          :key="action.key"
          class="my-actions__item tech-pressable tech-stagger-item"
          hover-class="tech-card-hover"
          :style="`animation-delay: ${(index + 1) * 55}ms;`"
          @tap="handleActionTap(action.key)"
        >
          <text class="my-actions__value">{{ action.value }}</text>
          <text class="my-actions__label">{{ action.label }}</text>
          <text class="my-actions__subtitle">{{ action.subtitle }}</text>
        </view>
      </view>

      <view v-if="loading" class="tech-panel tech-panel-pad tech-state-card tech-fade-up tech-delay-3">
        <text class="tech-state-text">个人中心数据同步中...</text>
      </view>
    </view>

    <TechTabBar active="my" />
  </view>
</template>

<style scoped>
.my-page {
  padding-bottom: 190rpx;
}

.my-vip {
  overflow: hidden;
  background:
    radial-gradient(circle at 16% 0%, rgba(186, 122, 255, 0.28), transparent 30%),
    linear-gradient(135deg, rgba(38, 30, 78, 0.9), rgba(10, 16, 34, 0.92));
}

.my-vip__head {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.my-vip__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 110rpx;
  height: 110rpx;
  border-radius: 34rpx;
  background: linear-gradient(135deg, rgba(220, 205, 255, 0.18), rgba(103, 208, 255, 0.16));
  color: #f6f4ff;
  font-size: 30rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.my-vip__copy {
  flex: 1;
}

.my-vip__title {
  display: block;
  margin-top: 14rpx;
  color: var(--tech-text-primary);
  font-size: 42rpx;
  font-weight: 700;
  line-height: 1.24;
}

.my-vip__summary {
  display: block;
  margin-top: 12rpx;
  color: rgba(231, 235, 255, 0.82);
  font-size: 24rpx;
  line-height: 1.72;
}

.my-vip__signals {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 26rpx;
}

.my-vip__signal {
  padding: 18rpx 18rpx 20rpx;
  border: 1rpx solid rgba(196, 183, 255, 0.16);
  border-radius: 24rpx;
  background: rgba(12, 17, 34, 0.42);
}

.my-vip__signal-label {
  display: block;
  color: var(--tech-text-tertiary);
  font-size: 20rpx;
  letter-spacing: 2rpx;
}

.my-vip__signal-value {
  display: block;
  margin-top: 12rpx;
  color: var(--tech-text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.my-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.my-actions__item {
  min-height: 238rpx;
  padding: 24rpx 22rpx;
  border: 1rpx solid rgba(184, 173, 255, 0.16);
  border-radius: 30rpx;
  background:
    linear-gradient(180deg, rgba(21, 18, 46, 0.84), rgba(9, 14, 29, 0.9));
}

.my-actions__value {
  display: block;
  color: #d9d8ff;
  font-size: 52rpx;
  font-weight: 700;
  line-height: 1;
}

.my-actions__label {
  display: block;
  margin-top: 18rpx;
  color: var(--tech-text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.my-actions__subtitle {
  display: block;
  margin-top: 12rpx;
  color: var(--tech-text-secondary);
  font-size: 23rpx;
  line-height: 1.72;
}

@media (max-width: 520px) {
  .my-vip__head,
  .my-vip__signals,
  .my-actions {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

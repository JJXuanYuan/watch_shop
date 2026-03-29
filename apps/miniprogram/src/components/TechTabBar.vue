<script setup lang="ts">
import { computed } from "vue";

type TechTabKey = "home" | "cart" | "my";

interface Props {
  active: TechTabKey;
}

interface TechTabItem {
  key: TechTabKey;
  label: string;
  badge: string;
  path: string;
}

const props = defineProps<Props>();

const tabItems: TechTabItem[] = [
  {
    key: "home",
    label: "首页",
    badge: "01",
    path: "/pages/index/index",
  },
  {
    key: "cart",
    label: "购物车",
    badge: "02",
    path: "/pages/cart/index",
  },
  {
    key: "my",
    label: "我的",
    badge: "03",
    path: "/pages/my/index",
  },
];

const currentRoute = computed(() => {
  const pages = getCurrentPages();
  return pages[pages.length - 1]?.route ? `/${pages[pages.length - 1].route}` : "";
});

function handleTabPress(item: TechTabItem) {
  if (currentRoute.value === item.path) {
    return;
  }

  uni.reLaunch({
    url: item.path,
  });
}
</script>

<template>
  <view class="tech-tabbar">
    <view class="tech-tabbar__inner">
      <view
        v-for="item in tabItems"
        :key="item.key"
        class="tech-tabbar__item tech-pressable"
        :class="{ 'tech-tabbar__item--active': item.key === active }"
        hover-class="tech-card-hover"
        @tap="handleTabPress(item)"
      >
        <text class="tech-tabbar__badge">{{ item.badge }}</text>
        <text class="tech-tabbar__label">{{ item.label }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.tech-tabbar {
  position: fixed;
  right: 18rpx;
  bottom: calc(18rpx + env(safe-area-inset-bottom));
  left: 18rpx;
  z-index: 20;
}

.tech-tabbar__inner {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
  padding: 12rpx;
  border: 1rpx solid rgba(172, 184, 255, 0.16);
  border-radius: 999rpx;
  background:
    linear-gradient(135deg, rgba(23, 20, 51, 0.94), rgba(8, 13, 27, 0.94)),
    rgba(10, 16, 30, 0.92);
  box-shadow:
    0 18rpx 40rpx rgba(0, 0, 0, 0.28),
    inset 0 1rpx 0 rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(24rpx);
}

.tech-tabbar__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
  min-height: 92rpx;
  border-radius: 999rpx;
}

.tech-tabbar__item--active {
  background: linear-gradient(135deg, rgba(103, 88, 255, 0.22), rgba(65, 182, 255, 0.18));
  box-shadow: inset 0 0 0 1rpx rgba(185, 176, 255, 0.22);
}

.tech-tabbar__badge {
  color: rgba(177, 189, 212, 0.78);
  font-size: 18rpx;
  letter-spacing: 2rpx;
  font-family: var(--tech-font-mono);
}

.tech-tabbar__label {
  color: var(--tech-text-primary);
  font-size: 24rpx;
  font-weight: 700;
}
</style>

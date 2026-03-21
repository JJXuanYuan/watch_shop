<script setup lang="ts">
const cards = [
  {
    title: "工程目标",
    description: "为后续商城首页、商品、购物车和订单流程预留可运行的 uni-app 工程基础。",
  },
  {
    title: "当前状态",
    description: "本页面为小程序首页占位页，用于验证 Vue 3 + TypeScript + uni-app 集成可启动。",
  },
  {
    title: "接口接入",
    description: "后续统一通过环境变量配置 API 地址，当前已保留 VITE_API_BASE_URL。",
  },
];

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
</script>

<template>
  <view class="page">
    <view class="hero">
      <text class="eyebrow">Watch Shop Mini Program</text>
      <text class="title">商城小程序基础工程已就绪</text>
      <text class="summary">
        当前阶段只构建工程、部署和页面入口，为后续商城业务开发预留基础骨架。
      </text>
    </view>

    <view v-for="card in cards" :key="card.title" class="card">
      <text class="card-title">{{ card.title }}</text>
      <text class="card-description">{{ card.description }}</text>
    </view>

    <view class="meta">
      <text class="meta-label">API Base URL</text>
      <text class="meta-value">{{ apiBaseUrl }}</text>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 48rpx 28rpx 40rpx;
  color: #2c2418;
}

.hero {
  padding: 44rpx 36rpx;
  border-radius: 36rpx;
  background: rgba(255, 252, 247, 0.9);
  box-shadow: 0 24rpx 64rpx rgba(95, 72, 33, 0.12);
}

.eyebrow {
  display: block;
  margin-bottom: 16rpx;
  color: #8c6a2a;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
  text-transform: uppercase;
}

.title {
  display: block;
  margin-bottom: 20rpx;
  font-size: 56rpx;
  font-weight: 700;
  line-height: 1.16;
}

.summary {
  display: block;
  color: #645746;
  font-size: 28rpx;
  line-height: 1.8;
}

.card {
  margin-top: 24rpx;
  padding: 32rpx;
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 16rpx 44rpx rgba(77, 59, 28, 0.08);
}

.card-title {
  display: block;
  margin-bottom: 12rpx;
  font-size: 32rpx;
  font-weight: 700;
}

.card-description {
  display: block;
  color: #5d5242;
  font-size: 26rpx;
  line-height: 1.8;
}

.meta {
  margin-top: 28rpx;
  padding: 28rpx 32rpx;
  border-radius: 28rpx;
  background: #20180d;
}

.meta-label {
  display: block;
  margin-bottom: 8rpx;
  color: #f0dfc2;
  font-size: 22rpx;
  letter-spacing: 2rpx;
  text-transform: uppercase;
}

.meta-value {
  display: block;
  color: #f8cf7e;
  font-size: 24rpx;
  word-break: break-all;
}
</style>

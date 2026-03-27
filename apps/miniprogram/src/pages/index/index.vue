<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onPullDownRefresh } from "@dcloudio/uni-app";

import { fetchCategories, fetchProducts } from "../../api/shop";
import { formatPrice, hasPrice } from "../../utils/price";
import type { CategoryItem, ProductListItem } from "../../types/shop";

const categories = ref<CategoryItem[]>([]);
const recommendedProducts = ref<ProductListItem[]>([]);
const loading = ref(false);
const errorMessage = ref("");

const quickCategories = computed(() => categories.value.slice(0, 6));

async function loadHomeData() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const [categoryResponse, productResponse] = await Promise.all([
      fetchCategories(),
      fetchProducts({ page: 1, page_size: 6 }),
    ]);

    categories.value = categoryResponse.items;
    recommendedProducts.value = productResponse.items;
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "首页数据加载失败";
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
}

function openCategoryPage(categoryId?: number) {
  const suffix = categoryId ? `?categoryId=${categoryId}` : "";
  uni.navigateTo({
    url: `/pages/category/index${suffix}`,
  });
}

function openProductDetail(productId: number) {
  uni.navigateTo({
    url: `/pages/product/detail?id=${productId}`,
  });
}

function openCartPage() {
  uni.navigateTo({
    url: "/pages/cart/index",
  });
}

function openOrderListPage() {
  uni.navigateTo({
    url: "/pages/order/list",
  });
}

onLoad(() => {
  void loadHomeData();
});

onPullDownRefresh(() => {
  void loadHomeData();
});
</script>

<template>
  <view class="page">
    <view class="hero">
      <text class="hero-kicker">Phase 1 Storefront</text>
      <text class="hero-title">腕表商城</text>
      <text class="hero-summary">
        当前已接入最小交易闭环：浏览商品、加入购物车、提交订单、查看订单。
      </text>

      <view class="search-shell" @tap="openCategoryPage()">
        <text class="search-icon">⌕</text>
        <text class="search-text">搜索商品名称 / 进入分类浏览</text>
      </view>

      <view class="hero-actions">
        <view class="hero-action-card" @tap="openCartPage()">
          <text class="hero-action-title">购物车</text>
          <text class="hero-action-text">查看已加购商品并去结算</text>
        </view>
        <view class="hero-action-card" @tap="openOrderListPage()">
          <text class="hero-action-title">我的订单</text>
          <text class="hero-action-text">查看当前微信登录用户的订单记录</text>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="section-head">
        <text class="section-title">分类入口</text>
        <text class="section-action" @tap="openCategoryPage()">查看全部</text>
      </view>

      <view v-if="quickCategories.length" class="category-grid">
        <view
          v-for="category in quickCategories"
          :key="category.id"
          class="category-card"
          @tap="openCategoryPage(category.id)"
        >
          <text class="category-name">{{ category.name }}</text>
          <text class="category-meta">SORT {{ category.sort_order }}</text>
        </view>
      </view>

      <view v-else class="empty-card">
        <text class="empty-text">暂无可用分类</text>
      </view>
    </view>

    <view class="section">
      <view class="section-head">
        <text class="section-title">推荐商品</text>
        <text class="section-note">取前台商品列表前几项作为推荐</text>
      </view>

      <view v-if="errorMessage && !recommendedProducts.length" class="state-card">
        <text class="state-title">数据加载失败</text>
        <text class="state-text">{{ errorMessage }}</text>
        <button class="state-button" size="mini" @tap="loadHomeData">重新加载</button>
      </view>

      <view v-else-if="loading && !recommendedProducts.length" class="state-card">
        <text class="state-text">商品数据加载中...</text>
      </view>

      <view v-else-if="recommendedProducts.length" class="product-list">
        <view
          v-for="product in recommendedProducts"
          :key="product.id"
          class="product-card"
          @tap="openProductDetail(product.id)"
        >
          <image :src="product.cover_image" class="product-image" mode="aspectFill" />
          <view class="product-body">
            <text class="product-category">{{ product.category.name }}</text>
            <text class="product-name">{{ product.name }}</text>
            <text v-if="product.subtitle" class="product-subtitle">
              {{ product.subtitle }}
            </text>
            <view class="product-price-row">
              <text class="product-price">¥{{ formatPrice(product.price) }}</text>
              <text
                v-if="hasPrice(product.original_price)"
                class="product-price-original"
              >
                ¥{{ formatPrice(product.original_price) }}
              </text>
            </view>
          </view>
        </view>
      </view>

      <view v-else class="empty-card">
        <text class="empty-text">暂无在售商品</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 28rpx 24rpx 44rpx;
  color: #2f2619;
}

.hero {
  padding: 36rpx 32rpx;
  border-radius: 36rpx;
  background:
    linear-gradient(140deg, rgba(255, 249, 239, 0.98), rgba(237, 223, 196, 0.95)),
    #fff;
  box-shadow: 0 28rpx 72rpx rgba(105, 79, 34, 0.12);
}

.hero-kicker {
  display: block;
  color: #8d6c2f;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
  text-transform: uppercase;
}

.hero-title {
  display: block;
  margin-top: 18rpx;
  font-size: 60rpx;
  font-weight: 700;
  line-height: 1.1;
}

.hero-summary {
  display: block;
  margin-top: 18rpx;
  color: #645745;
  font-size: 28rpx;
  line-height: 1.7;
}

.search-shell {
  display: flex;
  align-items: center;
  margin-top: 28rpx;
  padding: 24rpx 28rpx;
  border-radius: 999rpx;
  background: rgba(38, 29, 18, 0.92);
}

.search-icon {
  margin-right: 16rpx;
  color: #f3d7a0;
  font-size: 30rpx;
}

.search-text {
  color: #f7ecda;
  font-size: 26rpx;
}

.hero-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 22rpx;
}

.hero-action-card {
  padding: 24rpx 22rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.68);
}

.hero-action-title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
}

.hero-action-text {
  display: block;
  margin-top: 10rpx;
  color: #665946;
  font-size: 22rpx;
  line-height: 1.6;
}

.section {
  margin-top: 28rpx;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
  padding: 0 6rpx;
}

.section-title {
  font-size: 34rpx;
  font-weight: 700;
}

.section-action,
.section-note {
  color: #8d6c2f;
  font-size: 24rpx;
}

.category-grid {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -9rpx;
}

.category-card {
  width: calc(50% - 18rpx);
  margin: 0 9rpx 18rpx;
  padding: 28rpx 24rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 18rpx 44rpx rgba(81, 61, 26, 0.08);
  box-sizing: border-box;
}

.category-name {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
}

.category-meta {
  display: block;
  margin-top: 10rpx;
  color: #866b43;
  font-size: 22rpx;
  letter-spacing: 2rpx;
}

.product-list {
  display: flex;
  flex-direction: column;
}

.product-card + .product-card {
  margin-top: 18rpx;
}

.product-card {
  display: flex;
  overflow: hidden;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 18rpx 48rpx rgba(84, 62, 23, 0.09);
}

.product-image {
  width: 212rpx;
  min-width: 212rpx;
  height: 212rpx;
  background: #f0e6d7;
}

.product-body {
  flex: 1;
  padding: 24rpx;
}

.product-category {
  display: block;
  color: #8d6c2f;
  font-size: 22rpx;
  letter-spacing: 2rpx;
}

.product-name {
  display: block;
  margin-top: 10rpx;
  font-size: 30rpx;
  font-weight: 700;
  line-height: 1.4;
}

.product-subtitle {
  display: block;
  margin-top: 10rpx;
  color: #6e614e;
  font-size: 24rpx;
  line-height: 1.6;
}

.product-price-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 18rpx;
}

.product-price {
  margin-right: 14rpx;
  color: #20180d;
  font-size: 34rpx;
  font-weight: 700;
}

.product-price-original {
  color: #9e9280;
  font-size: 24rpx;
  text-decoration: line-through;
}

.empty-card,
.state-card {
  padding: 36rpx 28rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 18rpx 44rpx rgba(81, 61, 26, 0.07);
}

.empty-text,
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

@media (max-width: 520px) {
  .hero-actions {
    grid-template-columns: 1fr;
  }
}
</style>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onPullDownRefresh } from "@dcloudio/uni-app";

import { fetchProductDetail } from "../../api/shop";
import { addCartItem } from "../../api/trade";
import { formatPrice, hasPrice } from "../../utils/price";
import type { ProductDetail } from "../../types/shop";

interface DetailPageQuery {
  id?: string;
}

const product = ref<ProductDetail | null>(null);
const productId = ref<number | null>(null);
const loading = ref(false);
const errorMessage = ref("");
const addingToCart = ref(false);

const banners = computed(() => {
  if (!product.value) {
    return [];
  }

  if (product.value.banner_images.length) {
    return product.value.banner_images;
  }

  return product.value.cover_image ? [product.value.cover_image] : [];
});

async function loadProductDetail() {
  if (!productId.value) {
    errorMessage.value = "缺少商品 ID";
    product.value = null;
    uni.stopPullDownRefresh();
    return;
  }

  loading.value = true;
  errorMessage.value = "";

  try {
    product.value = await fetchProductDetail(productId.value);
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "商品详情加载失败";
    product.value = null;
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
}

function parseProductId(value?: string): number | null {
  if (!value) {
    return null;
  }

  const numericValue = Number(value);
  return Number.isFinite(numericValue) && numericValue > 0 ? numericValue : null;
}

function openCartPage() {
  uni.navigateTo({
    url: "/pages/cart/index",
  });
}

async function handleAddToCart() {
  if (!product.value || addingToCart.value) {
    return;
  }

  addingToCart.value = true;

  try {
    await addCartItem({
      product_id: product.value.id,
      quantity: 1,
    });
    uni.showToast({
      title: "已加入购物车",
      icon: "success",
    });
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "加入购物车失败",
      icon: "none",
    });
  } finally {
    addingToCart.value = false;
  }
}

onLoad((query) => {
  const pageQuery = (query ?? {}) as DetailPageQuery;
  productId.value = parseProductId(pageQuery.id);
  void loadProductDetail();
});

onPullDownRefresh(() => {
  void loadProductDetail();
});
</script>

<template>
  <view class="page">
    <view v-if="loading && !product" class="state-card">
      <text class="state-text">商品详情加载中...</text>
    </view>

    <view v-else-if="errorMessage && !product" class="state-card">
      <text class="state-title">商品详情加载失败</text>
      <text class="state-text">{{ errorMessage }}</text>
      <button class="state-button" size="mini" @tap="loadProductDetail">重新加载</button>
    </view>

    <view v-else-if="product" class="detail-shell">
      <swiper
        v-if="banners.length"
        class="hero-swiper"
        indicator-dots
        circular
        autoplay
        interval="4000"
        duration="500"
      >
        <swiper-item v-for="imageUrl in banners" :key="imageUrl">
          <image :src="imageUrl" class="hero-image" mode="aspectFill" />
        </swiper-item>
      </swiper>

      <view class="content-card">
        <text class="category-tag">{{ product.category.name }}</text>
        <text class="product-name">{{ product.name }}</text>

        <view class="price-row">
          <text class="price">¥{{ formatPrice(product.price) }}</text>
          <text v-if="hasPrice(product.original_price)" class="original-price">
            ¥{{ formatPrice(product.original_price) }}
          </text>
        </view>

        <text v-if="product.subtitle" class="subtitle">{{ product.subtitle }}</text>

        <view class="meta-row">
          <text class="meta-pill">销量 {{ product.sales }}</text>
          <text class="meta-pill">库存 {{ product.stock }}</text>
          <text class="meta-pill">状态 {{ product.status }}</text>
          <text class="meta-pill">加购数量默认 1 件</text>
        </view>
      </view>

      <view class="detail-card">
        <text class="section-title">图文详情</text>
        <text class="detail-text">
          {{ product.detail_content || "当前商品暂无更多图文详情。" }}
        </text>
      </view>
    </view>

    <view v-if="product" class="action-bar">
      <button class="action-secondary" :loading="addingToCart" @tap="handleAddToCart">
        加入购物车
      </button>
      <button class="action-primary" @tap="openCartPage">
        去购物车结算
      </button>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding-bottom: 150rpx;
  color: #2f2619;
}

.detail-shell {
  padding: 0 24rpx 32rpx;
}

.hero-swiper {
  height: 720rpx;
  margin: 24rpx 0 0;
  overflow: hidden;
  border-radius: 36rpx;
  box-shadow: 0 24rpx 68rpx rgba(89, 67, 27, 0.14);
}

.hero-image {
  width: 100%;
  height: 100%;
  background: #efe4d2;
}

.content-card,
.detail-card,
.state-card {
  margin-top: 24rpx;
  padding: 30rpx 28rpx;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 18rpx 48rpx rgba(81, 61, 26, 0.09);
}

.category-tag {
  display: inline-flex;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(240, 213, 157, 0.45);
  color: #7d5d22;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.product-name {
  display: block;
  margin-top: 18rpx;
  font-size: 44rpx;
  font-weight: 700;
  line-height: 1.3;
}

.price-row {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  margin-top: 20rpx;
}

.price {
  margin-right: 16rpx;
  color: #20180d;
  font-size: 46rpx;
  font-weight: 700;
}

.original-price {
  color: #9e9280;
  font-size: 26rpx;
  text-decoration: line-through;
}

.subtitle {
  display: block;
  margin-top: 18rpx;
  color: #625441;
  font-size: 28rpx;
  line-height: 1.8;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  margin-top: 22rpx;
}

.meta-pill {
  margin: 0 14rpx 14rpx 0;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: #f7f1e7;
  color: #6d604d;
  font-size: 24rpx;
}

.section-title {
  display: block;
  margin-bottom: 16rpx;
  font-size: 32rpx;
  font-weight: 700;
}

.detail-text {
  color: #5e513f;
  font-size: 28rpx;
  line-height: 1.9;
  white-space: pre-wrap;
}

.state-title {
  display: block;
  margin-bottom: 10rpx;
  font-size: 30rpx;
  font-weight: 700;
}

.state-text {
  color: #6d604d;
  font-size: 26rpx;
  line-height: 1.7;
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
  padding: 18rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));
  background: rgba(250, 245, 236, 0.96);
  box-shadow: 0 -12rpx 30rpx rgba(62, 47, 19, 0.08);
}

.action-secondary,
.action-primary {
  flex: 1;
  height: 84rpx;
  border: none;
  border-radius: 999rpx;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 84rpx;
}

.action-secondary {
  margin-right: 16rpx;
  color: #20180d;
  background: #ead7b1;
}

.action-primary {
  color: #fff7e8;
  background: #2c2114;
}
</style>

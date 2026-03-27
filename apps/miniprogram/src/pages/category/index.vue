<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onPullDownRefresh } from "@dcloudio/uni-app";

import { fetchCategories, fetchProducts } from "../../api/shop";
import { formatPrice, hasPrice } from "../../utils/price";
import type { CategoryItem, ProductListItem } from "../../types/shop";

interface CategoryPageQuery {
  categoryId?: string;
}

const categories = ref<CategoryItem[]>([]);
const products = ref<ProductListItem[]>([]);
const selectedCategoryId = ref<number | null>(null);
const initialCategoryId = ref<number | null>(null);
const loading = ref(false);
const productLoading = ref(false);
const errorMessage = ref("");

const selectedCategory = computed(() =>
  categories.value.find((item) => item.id === selectedCategoryId.value) ?? null,
);

function parseCategoryId(value?: string): number | null {
  if (!value) {
    return null;
  }

  const numericValue = Number(value);
  return Number.isFinite(numericValue) && numericValue > 0 ? numericValue : null;
}

async function loadProductsByCategory(categoryId: number) {
  productLoading.value = true;
  errorMessage.value = "";

  try {
    const response = await fetchProducts({
      category_id: categoryId,
      page: 1,
      page_size: 20,
    });

    selectedCategoryId.value = categoryId;
    products.value = response.items;
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "商品列表加载失败";
    products.value = [];
  } finally {
    productLoading.value = false;
  }
}

async function loadPageData() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const categoryResponse = await fetchCategories();
    categories.value = categoryResponse.items;

    if (!categories.value.length) {
      selectedCategoryId.value = null;
      products.value = [];
      return;
    }

    const fallbackCategory = categories.value[0];
    const matchedCategory = categories.value.find(
      (item) => item.id === initialCategoryId.value,
    );
    const nextCategoryId =
      matchedCategory?.id ?? selectedCategoryId.value ?? fallbackCategory.id;

    await loadProductsByCategory(nextCategoryId);
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "分类页数据加载失败";
    categories.value = [];
    products.value = [];
    selectedCategoryId.value = null;
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
}

function handleCategoryTap(categoryId: number) {
  if (selectedCategoryId.value === categoryId && products.value.length) {
    return;
  }

  void loadProductsByCategory(categoryId);
}

function openProductDetail(productId: number) {
  uni.navigateTo({
    url: `/pages/product/detail?id=${productId}`,
  });
}

onLoad((query) => {
  const pageQuery = (query ?? {}) as CategoryPageQuery;
  initialCategoryId.value = parseCategoryId(pageQuery.categoryId);
  void loadPageData();
});

onPullDownRefresh(() => {
  void loadPageData();
});
</script>

<template>
  <view class="page">
    <view class="header-card">
      <text class="header-kicker">Category View</text>
      <text class="header-title">分类商品浏览</text>
      <text class="header-summary">
        默认选中第一个可用分类，点击左侧分类后刷新右侧商品列表。
      </text>
    </view>

    <view v-if="errorMessage && !categories.length" class="state-card">
      <text class="state-title">分类数据加载失败</text>
      <text class="state-text">{{ errorMessage }}</text>
      <button class="state-button" size="mini" @tap="loadPageData">重新加载</button>
    </view>

    <view v-else-if="loading && !categories.length" class="state-card">
      <text class="state-text">分类数据加载中...</text>
    </view>

    <view v-else-if="!categories.length" class="state-card">
      <text class="state-text">暂无启用中的分类</text>
    </view>

    <view v-else class="catalog-panel">
      <scroll-view scroll-y class="category-scroll">
        <view
          v-for="category in categories"
          :key="category.id"
          class="category-item"
          :class="{ 'category-item--active': category.id === selectedCategoryId }"
          @tap="handleCategoryTap(category.id)"
        >
          <text class="category-item-name">{{ category.name }}</text>
          <text class="category-item-meta">#{{ category.sort_order }}</text>
        </view>
      </scroll-view>

      <scroll-view scroll-y class="product-scroll">
        <view class="product-header">
          <text class="product-header-title">
            {{ selectedCategory?.name || "分类商品" }}
          </text>
          <text class="product-header-summary">
            {{ productLoading ? "商品列表加载中..." : `共 ${products.length} 件商品` }}
          </text>
        </view>

        <view v-if="errorMessage && !productLoading" class="inner-state-card">
          <text class="state-text">{{ errorMessage }}</text>
        </view>

        <view v-else-if="productLoading" class="inner-state-card">
          <text class="state-text">正在加载商品...</text>
        </view>

        <view v-else-if="products.length" class="product-list">
          <view
            v-for="product in products"
            :key="product.id"
            class="product-card"
            @tap="openProductDetail(product.id)"
          >
            <image :src="product.cover_image" class="product-image" mode="aspectFill" />
            <view class="product-content">
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

        <view v-else class="inner-state-card">
          <text class="state-text">当前分类下暂无商品</text>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx;
  color: #2f2619;
}

.header-card {
  padding: 30rpx 28rpx;
  border-radius: 32rpx;
  background: rgba(255, 252, 246, 0.94);
  box-shadow: 0 22rpx 60rpx rgba(90, 68, 29, 0.11);
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

.catalog-panel {
  display: flex;
  height: calc(100vh - 320rpx);
  margin-top: 24rpx;
}

.category-scroll,
.product-scroll {
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 18rpx 44rpx rgba(81, 61, 26, 0.08);
}

.category-scroll {
  width: 208rpx;
  margin-right: 20rpx;
}

.product-scroll {
  flex: 1;
  padding: 24rpx;
  box-sizing: border-box;
}

.category-item {
  padding: 26rpx 20rpx;
  border-bottom: 1rpx solid rgba(141, 108, 47, 0.08);
}

.category-item--active {
  background: linear-gradient(180deg, rgba(240, 213, 157, 0.46), rgba(255, 248, 236, 0.9));
}

.category-item-name {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 1.5;
}

.category-item-meta {
  display: block;
  margin-top: 8rpx;
  color: #8a7554;
  font-size: 22rpx;
}

.product-header {
  margin-bottom: 20rpx;
}

.product-header-title {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
}

.product-header-summary {
  display: block;
  margin-top: 10rpx;
  color: #7d6f59;
  font-size: 24rpx;
}

.product-list {
  display: flex;
  flex-direction: column;
}

.product-card + .product-card {
  margin-top: 18rpx;
}

.product-card {
  overflow: hidden;
  border-radius: 24rpx;
  background: #fbf8f3;
}

.product-image {
  width: 100%;
  height: 250rpx;
  background: #efe4d2;
}

.product-content {
  padding: 22rpx 22rpx 24rpx;
}

.product-name {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  line-height: 1.45;
}

.product-subtitle {
  display: block;
  margin-top: 10rpx;
  color: #6d604c;
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
  margin-right: 12rpx;
  color: #20180d;
  font-size: 32rpx;
  font-weight: 700;
}

.product-price-original {
  color: #9d907d;
  font-size: 24rpx;
  text-decoration: line-through;
}

.state-card,
.inner-state-card {
  padding: 32rpx 28rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 18rpx 44rpx rgba(81, 61, 26, 0.07);
}

.state-card {
  margin-top: 24rpx;
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
</style>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onPullDownRefresh } from "@dcloudio/uni-app";

import ProductCard from "../../components/ProductCard.vue";
import TechSearchBar from "../../components/TechSearchBar.vue";
import { fetchCategories, fetchProducts } from "../../api/shop";
import type { CategoryItem, ProductListItem } from "../../types/shop";
import {
  STOREFRONT_CHANNELS,
  filterProductsByKeyword,
  getChannelPageTitle,
  getChannelProducts,
  getDefaultChannelKey,
  getStoreChannelDefinition,
  resolveChannelCategory,
  type StoreChannelKey,
} from "../../utils/storefront";

interface CategoryPageQuery {
  channel?: string;
  keyword?: string;
}

const categories = ref<CategoryItem[]>([]);
const products = ref<ProductListItem[]>([]);
const selectedChannelKey = ref<StoreChannelKey>("modeling");
const loading = ref(false);
const errorMessage = ref("");
const searchKeyword = ref("");

const currentChannel = computed(() => getStoreChannelDefinition(selectedChannelKey.value));
const matchedCategory = computed(() =>
  resolveChannelCategory(selectedChannelKey.value, categories.value),
);
const channelProducts = computed(() =>
  getChannelProducts(selectedChannelKey.value, products.value, categories.value),
);
const visibleProducts = computed(() =>
  filterProductsByKeyword(channelProducts.value, searchKeyword.value),
);
const pageTitle = computed(() =>
  getChannelPageTitle(selectedChannelKey.value, categories.value),
);

function decodeKeyword(value?: string): string {
  if (!value) {
    return "";
  }

  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

async function loadPageData() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const [categoryResponse, productResponse] = await Promise.all([
      fetchCategories(),
      fetchProducts({ page: 1, page_size: 48 }),
    ]);

    categories.value = categoryResponse.items;
    products.value = productResponse.items;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "分类商品加载失败";
    categories.value = [];
    products.value = [];
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
}

function openProductDetail(productId: number) {
  uni.navigateTo({
    url: `/pages/product/detail?id=${productId}`,
  });
}

function handleBack() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
    return;
  }

  uni.reLaunch({
    url: "/pages/index/index",
  });
}

function handleChannelChange(channelKey: StoreChannelKey) {
  selectedChannelKey.value = channelKey;
}

function handleSearch(keyword: string) {
  searchKeyword.value = keyword.trim();
}

onLoad((query) => {
  const pageQuery = (query ?? {}) as CategoryPageQuery;
  selectedChannelKey.value = getDefaultChannelKey(pageQuery.channel);
  searchKeyword.value = decodeKeyword(pageQuery.keyword);
  void loadPageData();
});

onPullDownRefresh(() => {
  void loadPageData();
});
</script>

<template>
  <view class="tech-page category-page">
    <view class="tech-shell">
      <view class="tech-nav category-nav tech-fade-up">
        <button
          class="tech-icon-button tech-icon-button--ghost"
          hover-class="tech-button-hover"
          @tap="handleBack"
        >
          &lt;
        </button>

        <view class="tech-nav__center">
          <text class="tech-nav__title">分类商品页</text>
          <text class="tech-nav__subtitle">{{ currentChannel.label }}</text>
        </view>

        <text class="category-nav__badge">{{ currentChannel.badge }}</text>
      </view>

      <TechSearchBar
        v-model="searchKeyword"
        class="tech-fade-up tech-delay-1"
        :placeholder="currentChannel.searchPlaceholder"
        @submit="handleSearch"
      />

      <scroll-view scroll-x class="category-tabs tech-fade-up tech-delay-2" show-scrollbar="false">
        <view class="category-tabs__inner">
          <view
            v-for="channel in STOREFRONT_CHANNELS"
            :key="channel.key"
            class="category-tabs__item tech-pressable"
            :class="{ 'category-tabs__item--active': channel.key === selectedChannelKey }"
            hover-class="tech-card-hover"
            @tap="handleChannelChange(channel.key)"
          >
            <text class="category-tabs__code">{{ channel.badge }}</text>
            <text class="category-tabs__label">{{ channel.label }}</text>
          </view>
        </view>
      </scroll-view>

      <view v-if="loading && !products.length" class="tech-panel tech-panel-pad tech-state-card tech-fade-up tech-delay-3">
        <text class="tech-state-text">商品列表加载中...</text>
      </view>

      <view v-else-if="errorMessage && !products.length" class="tech-panel tech-panel-pad tech-state-card tech-fade-up tech-delay-3">
        <text class="tech-state-title">分类商品加载失败</text>
        <text class="tech-state-text">{{ errorMessage }}</text>
        <button
          class="tech-button tech-button--ghost tech-mini-button retry-button"
          hover-class="tech-button-hover"
          @tap="loadPageData"
        >
          重新加载
        </button>
      </view>

      <template v-else>
        <view class="tech-panel tech-panel-pad category-hero tech-fade-up tech-delay-3">
          <view class="category-hero__head">
            <view>
              <text class="tech-kicker">统一承接页</text>
              <text class="category-hero__title">{{ pageTitle }}</text>
            </view>

            <text class="tech-chip tech-chip--accent">{{ visibleProducts.length }} 款商品</text>
          </view>

          <text class="category-hero__summary">{{ currentChannel.subtitle }}</text>

          <view class="category-hero__signals">
            <text v-if="matchedCategory" class="tech-chip tech-chip--muted">
              映射分类 {{ matchedCategory.name }}
            </text>
            <text v-if="searchKeyword" class="tech-chip tech-chip--purple">
              搜索 {{ searchKeyword }}
            </text>
          </view>
        </view>

        <view v-if="visibleProducts.length" class="category-products">
          <ProductCard
            v-for="(product, index) in visibleProducts"
            :key="product.id"
            :product="product"
            variant="catalog"
            :stagger-index="index + 1"
            label="分类商品"
            action-label="查看详情"
            @select="openProductDetail"
          />
        </view>

        <view v-else class="tech-panel tech-panel-pad tech-state-card tech-fade-up tech-delay-4">
          <text class="tech-state-title">当前条件下暂无商品</text>
          <text class="tech-state-text">可以切换上方频道，或调整搜索关键词继续查看。</text>
        </view>
      </template>
    </view>
  </view>
</template>

<style scoped>
.category-page {
  padding-bottom: 72rpx;
}

.category-nav__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 78rpx;
  height: 78rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, rgba(113, 86, 255, 0.24), rgba(74, 203, 255, 0.16));
  color: #eef2ff;
  font-size: 24rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.category-tabs {
  width: 100%;
}

.category-tabs__inner {
  display: inline-flex;
  gap: 14rpx;
  min-width: 100%;
}

.category-tabs__item {
  min-width: 164rpx;
  padding: 18rpx 20rpx;
  border: 1rpx solid rgba(176, 167, 255, 0.14);
  border-radius: 28rpx;
  background:
    linear-gradient(180deg, rgba(22, 18, 48, 0.8), rgba(9, 14, 30, 0.88));
}

.category-tabs__item--active {
  background: linear-gradient(135deg, rgba(104, 87, 255, 0.22), rgba(62, 186, 255, 0.18));
  box-shadow:
    inset 0 0 0 1rpx rgba(196, 184, 255, 0.22),
    0 16rpx 32rpx rgba(8, 11, 28, 0.22);
}

.category-tabs__code {
  display: block;
  color: var(--tech-text-tertiary);
  font-size: 18rpx;
  letter-spacing: 3rpx;
  font-family: var(--tech-font-mono);
}

.category-tabs__label {
  display: block;
  margin-top: 10rpx;
  color: var(--tech-text-primary);
  font-size: 28rpx;
  font-weight: 700;
}

.category-hero__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18rpx;
}

.category-hero__title {
  display: block;
  margin-top: 14rpx;
  color: var(--tech-text-primary);
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1.26;
}

.category-hero__summary {
  display: block;
  margin-top: 18rpx;
  color: var(--tech-text-secondary);
  font-size: 25rpx;
  line-height: 1.74;
}

.category-hero__signals {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 22rpx;
}

.category-products {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.retry-button {
  margin-top: 18rpx;
}

@media (max-width: 520px) {
  .category-hero__head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

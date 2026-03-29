<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onPullDownRefresh } from "@dcloudio/uni-app";

import ProductCard from "../../components/ProductCard.vue";
import TechImage from "../../components/TechImage.vue";
import TechSearchBar from "../../components/TechSearchBar.vue";
import TechTabBar from "../../components/TechTabBar.vue";
import WechatQrSheet from "../../components/WechatQrSheet.vue";
import { fetchProducts } from "../../api/shop";
import { getProductContent } from "../../utils/product-content";
import { formatPrice, hasPrice } from "../../utils/price";
import {
  STOREFRONT_CHANNELS,
  type StoreChannelKey,
} from "../../utils/storefront";
import type { ProductListItem } from "../../types/shop";

const products = ref<ProductListItem[]>([]);
const loading = ref(false);
const errorMessage = ref("");
const searchKeyword = ref("");
const qrVisible = ref(false);

const bannerProducts = computed(() => products.value.slice(0, 3));
const hotProducts = computed(() => products.value.slice(0, 2));

function getProductBundle(product: ProductListItem) {
  return getProductContent(product, product.category);
}

function getBannerTitle(product: ProductListItem): string {
  return getProductBundle(product).shortTitle || product.title;
}

function getBannerSummary(product: ProductListItem): string {
  return getProductBundle(product).subtitle || product.subtitle || "";
}

function getBannerImage(product: ProductListItem): string {
  return getProductBundle(product).heroImage || product.cover_image;
}

function getBannerImages(product: ProductListItem): string[] {
  return getProductBundle(product).galleryImages;
}

function sortProducts(items: ProductListItem[]): ProductListItem[] {
  return [...items].sort((left, right) => {
    const leftScore = 30 * Number(left.is_featured) + 12 * left.sales + Math.max(left.stock, 0);
    const rightScore = 30 * Number(right.is_featured) + 12 * right.sales + Math.max(right.stock, 0);

    if (rightScore !== leftScore) {
      return rightScore - leftScore;
    }

    return left.id - right.id;
  });
}

async function loadHomeData() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const productResponse = await fetchProducts({ page: 1, page_size: 18 });
    products.value = sortProducts(productResponse.items);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "首页数据加载失败";
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
}

function openCategoryPage(channelKey: StoreChannelKey = "modeling", keyword = "") {
  const query = [`channel=${channelKey}`];
  if (keyword.trim()) {
    query.push(`keyword=${encodeURIComponent(keyword.trim())}`);
  }

  uni.navigateTo({
    url: `/pages/category/index?${query.join("&")}`,
  });
}

function openProductDetail(productId: number) {
  uni.navigateTo({
    url: `/pages/product/detail?id=${productId}`,
  });
}

function handleSearch(keyword: string) {
  const normalizedKeyword = keyword.trim();
  if (!normalizedKeyword) {
    uni.showToast({
      title: "请输入搜索关键词",
      icon: "none",
    });
    return;
  }

  openCategoryPage("flash", normalizedKeyword);
}

function openQrSheet() {
  qrVisible.value = true;
}

onLoad(() => {
  void loadHomeData();
});

onPullDownRefresh(() => {
  void loadHomeData();
});
</script>

<template>
  <view class="tech-page home-page">
    <view class="tech-shell">
      <view class="tech-nav home-nav tech-fade-up">
        <view class="tech-nav__side"></view>

        <view class="tech-nav__center">
          <text class="tech-nav__title">我享造商城</text>
          <text class="tech-nav__subtitle">NEON FUTURE STORE</text>
        </view>

        <button
          class="tech-icon-button"
          hover-class="tech-button-hover"
          @tap="openQrSheet"
        >
          QR
        </button>
      </view>

      <TechSearchBar
        v-model="searchKeyword"
        class="tech-fade-up tech-delay-1"
        placeholder="搜索主推商品或频道"
        @submit="handleSearch"
      />

      <view v-if="loading && !products.length" class="tech-panel tech-panel-pad tech-state-card tech-fade-up tech-delay-2">
        <text class="tech-state-text">首页内容加载中...</text>
      </view>

      <view v-else-if="errorMessage && !products.length" class="tech-panel tech-panel-pad tech-state-card tech-fade-up tech-delay-2">
        <text class="tech-state-title">首页加载失败</text>
        <text class="tech-state-text">{{ errorMessage }}</text>
        <button
          class="tech-button tech-button--ghost tech-mini-button retry-button"
          hover-class="tech-button-hover"
          @tap="loadHomeData"
        >
          重新加载
        </button>
      </view>

      <template v-else>
        <swiper
          v-if="bannerProducts.length"
          class="tech-panel home-banner tech-fade-scale tech-delay-2"
          circular
          autoplay
          interval="4200"
          duration="320"
          indicator-dots
          indicator-color="rgba(214, 220, 255, 0.2)"
          indicator-active-color="#9f8eff"
        >
          <swiper-item
            v-for="(product, index) in bannerProducts"
            :key="product.id"
          >
            <view
              class="home-banner__slide tech-pressable"
              hover-class="tech-card-hover"
              @tap="openProductDetail(product.id)"
            >
              <TechImage
                :src="getBannerImage(product)"
                :sources="getBannerImages(product)"
                class="home-banner__image"
                :label="getBannerTitle(product)"
                :sub-label="product.category.name"
                :show-caption="false"
              />

              <view class="home-banner__overlay"></view>

              <view class="home-banner__copy">
                <view class="home-banner__topline">
                  <text class="tech-chip tech-chip--accent">
                    {{ STOREFRONT_CHANNELS[index % STOREFRONT_CHANNELS.length].heroLabel }}
                  </text>
                  <text class="home-banner__badge">
                    {{ STOREFRONT_CHANNELS[index % STOREFRONT_CHANNELS.length].badge }}
                  </text>
                </view>

                <text class="home-banner__title">{{ getBannerTitle(product) }}</text>
                <text class="home-banner__summary">{{ getBannerSummary(product) }}</text>

                <view class="home-banner__price-row">
                  <text class="tech-price home-banner__price">¥{{ formatPrice(product.price) }}</text>
                  <text v-if="hasPrice(product.original_price)" class="tech-price-original">
                    ¥{{ formatPrice(product.original_price) }}
                  </text>
                </view>

                <button
                  class="tech-button tech-button--primary home-banner__action"
                  hover-class="tech-button-hover"
                  @tap.stop="openProductDetail(product.id)"
                >
                  立即查看
                </button>
              </view>
            </view>
          </swiper-item>
        </swiper>

        <view class="home-shortcuts">
          <view
            v-for="(channel, index) in STOREFRONT_CHANNELS"
            :key="channel.key"
            class="home-shortcuts__item tech-pressable tech-fade-up"
            :class="`tech-delay-${Math.min(index + 2, 5)}`"
            hover-class="tech-card-hover"
            @tap="openCategoryPage(channel.key)"
          >
            <view class="home-shortcuts__badge">{{ channel.badge }}</view>
            <text class="home-shortcuts__title">{{ channel.label }}</text>
            <text class="home-shortcuts__meta">{{ channel.subtitle }}</text>
          </view>
        </view>

        <view class="tech-panel tech-panel-pad home-hot tech-fade-up tech-delay-3">
          <view class="home-section__head">
            <view>
              <text class="tech-kicker">近期爆款推荐</text>
              <text class="home-section__title">只保留 2 个高优先级商品</text>
            </view>
            <text class="home-section__link" @tap="openCategoryPage('flash')">查看全部</text>
          </view>

          <view v-if="hotProducts.length" class="home-hot__grid">
            <ProductCard
              v-for="(product, index) in hotProducts"
              :key="product.id"
              :product="product"
              variant="catalog"
              :stagger-index="index + 1"
              label="近期爆款"
              action-label="立即查看"
              @select="openProductDetail"
            />
          </view>

          <view v-else class="tech-panel tech-panel-subtle tech-state-card">
            <text class="tech-state-title">暂无爆款商品</text>
            <text class="tech-state-text">当前没有可展示的主推商品。</text>
          </view>
        </view>
      </template>
    </view>

    <WechatQrSheet
      v-model="qrVisible"
      title="官方微信二维码"
      description="首页按钮和弹层已经接通，后续替换成真实微信二维码图片即可。"
    />

    <TechTabBar active="home" />
  </view>
</template>

<style scoped>
.home-page {
  padding-bottom: 190rpx;
}

.home-nav {
  align-items: center;
}

.home-banner {
  position: relative;
  min-height: 820rpx;
  overflow: hidden;
}

.home-banner__slide {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 820rpx;
}

.home-banner__image,
.home-banner__overlay {
  position: absolute;
  inset: 0;
}

.home-banner__image {
  width: 100%;
  height: 100%;
}

.home-banner__overlay {
  background:
    radial-gradient(circle at 16% 0%, rgba(189, 118, 255, 0.26), transparent 28%),
    linear-gradient(180deg, rgba(6, 10, 23, 0.18), rgba(5, 8, 18, 0.18) 34%, rgba(5, 8, 18, 0.76));
}

.home-banner__copy {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  height: 100%;
  padding: 40rpx 36rpx 42rpx;
}

.home-banner__topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.home-banner__badge {
  color: rgba(255, 255, 255, 0.82);
  font-size: 20rpx;
  letter-spacing: 4rpx;
  font-family: var(--tech-font-mono);
}

.home-banner__title {
  display: block;
  max-width: 88%;
  margin-top: 24rpx;
  color: #ffffff;
  font-size: 58rpx;
  font-weight: 700;
  line-height: 1.08;
}

.home-banner__summary {
  display: block;
  max-width: 84%;
  margin-top: 18rpx;
  color: rgba(225, 229, 255, 0.92);
  font-size: 26rpx;
  line-height: 1.72;
}

.home-banner__price-row {
  display: flex;
  align-items: baseline;
  gap: 14rpx;
  margin-top: 24rpx;
}

.home-banner__price {
  font-size: 56rpx;
}

.home-banner__action {
  width: 100%;
  margin-top: 28rpx;
}

.home-shortcuts {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16rpx;
}

.home-shortcuts__item {
  min-height: 238rpx;
  padding: 24rpx 18rpx 22rpx;
  border: 1rpx solid rgba(175, 159, 255, 0.14);
  border-radius: 30rpx;
  background:
    radial-gradient(circle at 20% 0%, rgba(170, 100, 255, 0.22), transparent 30%),
    linear-gradient(180deg, rgba(22, 18, 48, 0.84), rgba(10, 14, 29, 0.9));
  box-shadow:
    inset 0 1rpx 0 rgba(255, 255, 255, 0.04),
    0 18rpx 34rpx rgba(6, 9, 24, 0.2);
}

.home-shortcuts__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 78rpx;
  height: 78rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, rgba(122, 94, 255, 0.26), rgba(66, 208, 255, 0.18));
  color: #f4f7ff;
  font-size: 26rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
  box-shadow: inset 0 0 0 1rpx rgba(188, 177, 255, 0.22);
}

.home-shortcuts__title {
  display: block;
  margin-top: 22rpx;
  color: var(--tech-text-primary);
  font-size: 28rpx;
  font-weight: 700;
  line-height: 1.36;
}

.home-shortcuts__meta {
  display: block;
  margin-top: 12rpx;
  color: var(--tech-text-secondary);
  font-size: 21rpx;
  line-height: 1.68;
}

.home-hot__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
  margin-top: 24rpx;
}

.home-section__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18rpx;
}

.home-section__title {
  display: block;
  margin-top: 14rpx;
  color: var(--tech-text-primary);
  font-size: 38rpx;
  font-weight: 700;
  line-height: 1.28;
}

.home-section__link {
  color: #b7b9ff;
  font-size: 24rpx;
  font-weight: 600;
}

.retry-button {
  margin-top: 18rpx;
}

@media (max-width: 520px) {
  .home-banner__title,
  .home-banner__summary {
    max-width: 100%;
  }

  .home-shortcuts,
  .home-hot__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .home-section__head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

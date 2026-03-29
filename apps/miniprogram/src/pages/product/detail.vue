<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onPullDownRefresh } from "@dcloudio/uni-app";

import TechImage from "../../components/TechImage.vue";
import WechatQrSheet from "../../components/WechatQrSheet.vue";
import { fetchProductDetail } from "../../api/shop";
import { addCartItem } from "../../api/trade";
import { getProductContent } from "../../utils/product-content";
import {
  isFavoriteProduct,
  toggleFavoriteProduct,
} from "../../utils/favorites";
import { formatPrice, hasPrice } from "../../utils/price";
import { normalizeStringList } from "../../utils/text";
import type { ProductDetail, ProductStoryBlock } from "../../types/shop";

interface DetailPageQuery {
  id?: string;
}

interface DetailSpecEntry {
  label: string;
  value: string;
}

const product = ref<ProductDetail | null>(null);
const productId = ref<number | null>(null);
const loading = ref(false);
const errorMessage = ref("");
const buying = ref(false);
const favoriteActive = ref(false);
const customerSheetVisible = ref(false);

const productContent = computed(() =>
  product.value ? getProductContent(product.value, product.value.category) : null,
);
const visualImages = computed(() => {
  if (!product.value) {
    return [];
  }

  const galleryImages = productContent.value?.galleryImages.filter(Boolean) ?? [];
  if (galleryImages.length) {
    return galleryImages;
  }

  return [productContent.value?.heroImage || product.value.cover_image || ""].filter(Boolean);
});
const displayTitle = computed(() =>
  productContent.value?.shortTitle || product.value?.title || "商品详情",
);
const displaySummary = computed(() =>
  product.value?.subtitle || product.value?.detail_content || product.value?.detail || "",
);
const actualSellingPoints = computed(() =>
  product.value ? normalizeStringList(product.value.selling_points) : [],
);
const detailSpecs = computed<DetailSpecEntry[]>(() => {
  if (!product.value) {
    return [];
  }

  const entries = [
    { label: "材质", value: product.value.material ?? "" },
    { label: "镜面", value: product.value.crystal ?? "" },
    { label: "机芯/功能", value: product.value.movement_or_function ?? "" },
    { label: "动力储备", value: product.value.power_reserve ?? "" },
    { label: "防水等级", value: product.value.water_resistance ?? "" },
    { label: "表带材质", value: product.value.strap_material ?? "" },
  ];

  return entries.filter((item) => item.value.trim());
});
const detailText = computed(() => {
  if (!product.value) {
    return "";
  }

  const primaryText = product.value.detail_content?.trim() || "";
  const secondaryText = product.value.detail?.trim() || "";
  if (primaryText && secondaryText && primaryText !== secondaryText) {
    return `${primaryText}\n\n${secondaryText}`;
  }

  return primaryText || secondaryText;
});
const storyBlocks = computed(() => {
  if (!product.value || !Array.isArray(product.value.story_blocks)) {
    return [];
  }

  return product.value.story_blocks.filter((block: ProductStoryBlock) => (
    Boolean(block.title)
    || Boolean(block.subtitle)
    || Boolean(block.content)
    || Boolean(block.image)
    || Boolean(block.label)
  ));
});
const hasDetailSection = computed(() => (
  Boolean(detailText.value)
  || actualSellingPoints.value.length > 0
  || detailSpecs.value.length > 0
  || storyBlocks.value.length > 0
));

function parseProductId(value?: string): number | null {
  if (!value) {
    return null;
  }

  const numericValue = Number(value);
  return Number.isFinite(numericValue) && numericValue > 0 ? numericValue : null;
}

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
    const detail = await fetchProductDetail(productId.value);
    product.value = detail;
    favoriteActive.value = isFavoriteProduct(detail.id);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "商品详情加载失败";
    product.value = null;
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
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

function openCustomerSheet() {
  customerSheetVisible.value = true;
}

function handleFavoriteToggle() {
  if (!product.value) {
    return;
  }

  favoriteActive.value = toggleFavoriteProduct({
    id: product.value.id,
    title: displayTitle.value,
    subtitle: displaySummary.value,
    coverImage: visualImages.value[0] || "",
  });

  uni.showToast({
    title: favoriteActive.value ? "已加入收藏" : "已取消收藏",
    icon: "none",
  });
}

async function handleBuyNow() {
  if (!product.value || buying.value) {
    return;
  }

  if (product.value.status !== "on_sale" || product.value.stock <= 0) {
    uni.showToast({
      title: "当前商品暂不可购买",
      icon: "none",
    });
    return;
  }

  buying.value = true;

  try {
    await addCartItem({
      product_id: product.value.id,
      quantity: 1,
    });

    uni.navigateTo({
      url: "/pages/order/confirm",
    });
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "立即购买失败",
      icon: "none",
    });
  } finally {
    buying.value = false;
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
  <view class="tech-page product-detail-page">
    <view class="tech-shell">
      <view class="tech-nav detail-nav tech-fade-up">
        <button
          class="tech-icon-button tech-icon-button--ghost"
          hover-class="tech-button-hover"
          @tap="handleBack"
        >
          &lt;
        </button>

        <view class="tech-nav__center">
          <text class="tech-nav__title">{{ displayTitle }}</text>
          <text class="tech-nav__subtitle">{{ product?.category.name || "PRODUCT DETAIL" }}</text>
        </view>

        <button
          class="tech-icon-button"
          hover-class="tech-button-hover"
          @tap="openCustomerSheet"
        >
          KF
        </button>
      </view>

      <view v-if="loading && !product" class="tech-panel tech-panel-pad tech-state-card tech-fade-up tech-delay-1">
        <text class="tech-state-text">商品详情加载中...</text>
      </view>

      <view v-else-if="errorMessage && !product" class="tech-panel tech-panel-pad tech-state-card tech-fade-up tech-delay-1">
        <text class="tech-state-title">商品详情加载失败</text>
        <text class="tech-state-text">{{ errorMessage }}</text>
        <button
          class="tech-button tech-button--ghost tech-mini-button retry-button"
          hover-class="tech-button-hover"
          @tap="loadProductDetail"
        >
          重新加载
        </button>
      </view>

      <template v-else-if="product">
        <view class="tech-panel detail-hero tech-fade-scale tech-delay-1">
          <swiper
            v-if="visualImages.length > 1"
            class="detail-hero__swiper"
            circular
            autoplay
            interval="4200"
            duration="320"
            indicator-dots
            indicator-color="rgba(214, 220, 255, 0.18)"
            indicator-active-color="#9f8eff"
          >
            <swiper-item
              v-for="imageUrl in visualImages"
              :key="imageUrl"
            >
              <TechImage
                :src="imageUrl"
                :sources="visualImages"
                class="detail-hero__image"
                :label="displayTitle"
                :sub-label="product.category.name"
                :show-caption="false"
              />
            </swiper-item>
          </swiper>

          <TechImage
            v-else
            :src="visualImages[0]"
            :sources="visualImages"
            class="detail-hero__image"
            :label="displayTitle"
            :sub-label="product.category.name"
            :show-caption="false"
          />
        </view>

        <view class="tech-panel tech-panel-pad detail-price-card tech-fade-up tech-delay-2">
          <text class="tech-kicker">{{ product.category.name }}</text>
          <text class="detail-price-card__title">{{ displayTitle }}</text>
          <text v-if="displaySummary" class="detail-price-card__summary">{{ displaySummary }}</text>

          <view class="detail-price-card__row">
            <text class="tech-price detail-price-card__price">¥{{ formatPrice(product.price) }}</text>
            <text v-if="hasPrice(product.original_price)" class="tech-price-original">
              ¥{{ formatPrice(product.original_price) }}
            </text>
          </view>

          <view v-if="actualSellingPoints.length" class="detail-price-card__points">
            <text
              v-for="point in actualSellingPoints"
              :key="point"
              class="tech-chip tech-chip--accent"
            >
              {{ point }}
            </text>
          </view>

          <button
            class="tech-button tech-button--primary detail-price-card__action"
            hover-class="tech-button-hover"
            :loading="buying"
            @tap="handleBuyNow"
          >
            立即购买
          </button>
        </view>

        <view v-if="hasDetailSection" class="tech-panel tech-panel-pad detail-section tech-fade-up tech-delay-3">
          <view class="detail-section__head">
            <view>
              <text class="tech-kicker">产品详情</text>
              <text class="detail-section__title">真实字段优先展示</text>
            </view>
          </view>

          <text v-if="detailText" class="detail-section__text">{{ detailText }}</text>

          <view v-if="detailSpecs.length" class="detail-section__specs">
            <view
              v-for="spec in detailSpecs"
              :key="spec.label"
              class="detail-section__spec"
            >
              <text class="detail-section__spec-label">{{ spec.label }}</text>
              <text class="detail-section__spec-value">{{ spec.value }}</text>
            </view>
          </view>

          <view v-if="storyBlocks.length" class="detail-section__story">
            <view
              v-for="(block, index) in storyBlocks"
              :key="`${block.title || block.label || 'story'}-${index}`"
              class="detail-section__story-card"
            >
              <TechImage
                v-if="block.image"
                :src="block.image"
                class="detail-section__story-image"
                :label="block.title || displayTitle"
                :sub-label="block.label || product.category.name"
                :show-caption="false"
              />

              <view class="detail-section__story-copy">
                <text v-if="block.label" class="detail-section__story-kicker">{{ block.label }}</text>
                <text v-if="block.title" class="detail-section__story-title">{{ block.title }}</text>
                <text v-if="block.subtitle" class="detail-section__story-subtitle">{{ block.subtitle }}</text>
                <text v-if="block.content" class="detail-section__story-text">{{ block.content }}</text>
              </view>
            </view>
          </view>
        </view>
      </template>
    </view>

    <view v-if="product" class="detail-action-bar">
      <button
        class="tech-button tech-button--ghost detail-action-bar__minor"
        hover-class="tech-button-hover"
        @tap="handleFavoriteToggle"
      >
        {{ favoriteActive ? "已收藏" : "收藏" }}
      </button>

      <button
        class="tech-button tech-button--ghost detail-action-bar__minor"
        hover-class="tech-button-hover"
        @tap="openCustomerSheet"
      >
        客服
      </button>

      <button
        class="tech-button tech-button--primary detail-action-bar__primary"
        hover-class="tech-button-hover"
        :loading="buying"
        @tap="handleBuyNow"
      >
        立即购买
      </button>
    </view>

    <WechatQrSheet
      v-model="customerSheetVisible"
      title="客服微信二维码"
      description="详情页客服按钮已接通弹层，后续替换为真实客服二维码即可。"
    />
  </view>
</template>

<style scoped>
.product-detail-page {
  padding-bottom: 186rpx;
}

.detail-hero {
  overflow: hidden;
  padding: 18rpx;
}

.detail-hero__swiper,
.detail-hero__image {
  width: 100%;
  height: 880rpx;
  border-radius: 32rpx;
}

.detail-price-card__title,
.detail-section__title {
  display: block;
  margin-top: 16rpx;
  color: var(--tech-text-primary);
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1.26;
}

.detail-price-card__summary {
  display: block;
  margin-top: 14rpx;
  color: var(--tech-text-secondary);
  font-size: 25rpx;
  line-height: 1.76;
}

.detail-price-card__row {
  display: flex;
  align-items: baseline;
  gap: 14rpx;
  margin-top: 24rpx;
}

.detail-price-card__price {
  font-size: 58rpx;
}

.detail-price-card__points {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 24rpx;
}

.detail-price-card__action {
  width: 100%;
  margin-top: 28rpx;
}

.detail-section__text {
  display: block;
  margin-top: 20rpx;
  color: var(--tech-text-secondary);
  font-size: 26rpx;
  line-height: 1.9;
  white-space: pre-wrap;
}

.detail-section__specs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 24rpx;
}

.detail-section__spec {
  padding: 22rpx 20rpx;
  border: 1rpx solid rgba(180, 172, 255, 0.12);
  border-radius: 24rpx;
  background: rgba(15, 18, 40, 0.74);
}

.detail-section__spec-label {
  display: block;
  color: var(--tech-text-tertiary);
  font-size: 20rpx;
  letter-spacing: 2rpx;
}

.detail-section__spec-value {
  display: block;
  margin-top: 12rpx;
  color: var(--tech-text-primary);
  font-size: 28rpx;
  font-weight: 600;
  line-height: 1.6;
}

.detail-section__story {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 24rpx;
}

.detail-section__story-card {
  overflow: hidden;
  border: 1rpx solid rgba(180, 172, 255, 0.12);
  border-radius: 28rpx;
  background: rgba(15, 18, 40, 0.74);
}

.detail-section__story-image {
  width: 100%;
  height: 320rpx;
}

.detail-section__story-copy {
  padding: 22rpx 22rpx 24rpx;
}

.detail-section__story-kicker {
  color: var(--tech-text-tertiary);
  font-size: 18rpx;
  letter-spacing: 2rpx;
}

.detail-section__story-title {
  display: block;
  margin-top: 12rpx;
  color: var(--tech-text-primary);
  font-size: 32rpx;
  font-weight: 700;
  line-height: 1.34;
}

.detail-section__story-subtitle,
.detail-section__story-text {
  display: block;
  margin-top: 12rpx;
  color: var(--tech-text-secondary);
  font-size: 24rpx;
  line-height: 1.8;
  white-space: pre-wrap;
}

.detail-action-bar {
  position: fixed;
  right: 18rpx;
  bottom: calc(18rpx + env(safe-area-inset-bottom));
  left: 18rpx;
  z-index: 20;
  display: grid;
  grid-template-columns: 150rpx 150rpx 1fr;
  gap: 12rpx;
  padding: 12rpx;
  border: 1rpx solid rgba(180, 172, 255, 0.16);
  border-radius: 999rpx;
  background:
    linear-gradient(135deg, rgba(22, 18, 48, 0.94), rgba(8, 13, 28, 0.94));
  box-shadow: 0 18rpx 40rpx rgba(0, 0, 0, 0.28);
  backdrop-filter: blur(24rpx);
}

.detail-action-bar__minor,
.detail-action-bar__primary {
  min-width: 0;
}

.retry-button {
  margin-top: 18rpx;
}

@media (max-width: 520px) {
  .detail-section__specs,
  .detail-action-bar {
    grid-template-columns: 1fr;
  }
}
</style>

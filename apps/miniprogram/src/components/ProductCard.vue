<script setup lang="ts">
import { computed } from "vue";

import TechImage from "./TechImage.vue";
import { getProductContent } from "../utils/product-content";
import { formatPrice, hasPrice } from "../utils/price";
import type { ProductListItem } from "../types/shop";

type ProductCardVariant = "featured" | "catalog" | "compact" | "split";

interface Props {
  product: ProductListItem;
  variant?: ProductCardVariant;
  staggerIndex?: number;
  label?: string;
  actionLabel?: string;
}

const props = withDefaults(defineProps<Props>(), {
  variant: "catalog",
  staggerIndex: 0,
  label: "商品主图",
  actionLabel: "查看详情",
});

const emit = defineEmits<{
  select: [productId: number];
}>();

const resolvedVariant = computed(() =>
  props.variant === "split" ? "catalog" : props.variant,
);
const delayStyle = computed(() => `animation-delay: ${props.staggerIndex * 55}ms;`);
const productContent = computed(() => getProductContent(props.product, props.product.category));
const displayTitle = computed(() => productContent.value.shortTitle || props.product.title);
const displaySummary = computed(() => productContent.value.subtitle || props.product.subtitle || "");
const displayPoints = computed(() => {
  const limit = resolvedVariant.value === "compact" ? 1 : resolvedVariant.value === "featured" ? 3 : 2;
  return productContent.value.sellingPoints.slice(0, limit);
});
const displayImageSources = computed(() => {
  const galleryImages = productContent.value.galleryImages.filter(Boolean);
  if (galleryImages.length) {
    return galleryImages;
  }

  return [props.product.cover_image].filter(Boolean);
});
const badgeLabel = computed(() => {
  if (props.product.is_featured) {
    return "旗舰";
  }

  if (props.product.sales >= 100) {
    return "热卖";
  }

  return "精选";
});

function handleSelect() {
  emit("select", props.product.id);
}
</script>

<template>
  <view
    class="product-card tech-stagger-item tech-pressable"
    :class="`product-card--${resolvedVariant}`"
    :style="delayStyle"
    hover-class="tech-card-hover"
    @tap="handleSelect"
  >
    <view class="product-card__media">
      <TechImage
        :src="displayImageSources[0]"
        :sources="displayImageSources"
        class="product-card__image"
        :label="label"
        :sub-label="product.category.name"
        :show-caption="false"
      />

      <view class="product-card__overlay"></view>

      <view class="product-card__media-tags">
        <text class="tech-chip tech-chip--muted">{{ product.category.name }}</text>
        <text class="product-card__badge">{{ badgeLabel }}</text>
      </view>
    </view>

    <view class="product-card__body">
      <text class="product-card__title">{{ displayTitle }}</text>
      <text class="product-card__summary">{{ displaySummary }}</text>

      <view v-if="displayPoints.length" class="product-card__points">
        <text
          v-for="point in displayPoints"
          :key="point"
          class="product-card__point"
        >
          {{ point }}
        </text>
      </view>

      <view class="product-card__foot">
        <view class="product-card__price-block">
          <text class="tech-price product-card__price">¥{{ formatPrice(product.price) }}</text>
          <text v-if="hasPrice(product.original_price)" class="tech-price-original">
            ¥{{ formatPrice(product.original_price) }}
          </text>
        </view>

        <button
          class="tech-button tech-button--primary tech-mini-button product-card__action"
          hover-class="tech-button-hover"
          @tap.stop="handleSelect"
        >
          {{ actionLabel }}
        </button>
      </view>
    </view>
  </view>
</template>

<style scoped>
.product-card {
  overflow: hidden;
  border-radius: 34rpx;
  border: 1rpx solid rgba(175, 159, 255, 0.14);
  background:
    linear-gradient(180deg, rgba(21, 18, 46, 0.86), rgba(9, 14, 29, 0.92));
  box-shadow:
    inset 0 1rpx 0 rgba(255, 255, 255, 0.04),
    0 18rpx 34rpx rgba(6, 8, 25, 0.18);
}

.product-card__media {
  position: relative;
}

.product-card__image,
.product-card__overlay {
  width: 100%;
  height: 100%;
}

.product-card__overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(7, 12, 24, 0.04), rgba(7, 12, 24, 0.38)),
    radial-gradient(circle at 18% 0%, rgba(158, 102, 255, 0.22), transparent 28%);
  pointer-events: none;
}

.product-card__media-tags {
  position: absolute;
  top: 20rpx;
  right: 20rpx;
  left: 20rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.product-card__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42rpx;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(8, 13, 28, 0.46);
  color: rgba(241, 244, 255, 0.9);
  font-size: 18rpx;
  letter-spacing: 2rpx;
  backdrop-filter: blur(12rpx);
}

.product-card__body {
  padding: 24rpx 24rpx 26rpx;
}

.product-card__title {
  display: block;
  color: var(--tech-text-primary);
  font-size: 32rpx;
  font-weight: 700;
  line-height: 1.36;
}

.product-card__summary {
  display: block;
  margin-top: 12rpx;
  color: var(--tech-text-secondary);
  font-size: 24rpx;
  line-height: 1.72;
}

.product-card__points {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 18rpx;
}

.product-card__point {
  display: inline-flex;
  align-items: center;
  min-height: 40rpx;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(104, 86, 255, 0.14);
  color: #d7d7ff;
  font-size: 20rpx;
}

.product-card__foot {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18rpx;
  margin-top: 22rpx;
  padding-top: 18rpx;
  border-top: 1rpx solid rgba(176, 182, 255, 0.08);
}

.product-card__price-block {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.product-card__price {
  font-size: 40rpx;
}

.product-card__action {
  min-width: 174rpx;
}

.product-card--featured .product-card__image {
  height: 460rpx;
}

.product-card--featured .product-card__title {
  font-size: 38rpx;
}

.product-card--featured .product-card__price {
  font-size: 46rpx;
}

.product-card--catalog .product-card__image {
  height: 360rpx;
}

.product-card--compact .product-card__image {
  height: 280rpx;
}

.product-card--compact .product-card__title {
  font-size: 28rpx;
}

.product-card--compact .product-card__summary {
  font-size: 22rpx;
}

.product-card--compact .product-card__price {
  font-size: 34rpx;
}

.product-card--compact .product-card__action {
  min-width: 146rpx;
}

@media (max-width: 520px) {
  .product-card__foot {
    flex-direction: column;
    align-items: flex-start;
  }

  .product-card__action {
    width: 100%;
  }
}
</style>

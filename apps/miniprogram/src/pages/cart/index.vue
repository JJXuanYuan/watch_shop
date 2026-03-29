<script setup lang="ts">
import { computed, ref } from "vue";
import { onPullDownRefresh, onShow } from "@dcloudio/uni-app";

import ProductCard from "../../components/ProductCard.vue";
import TechImage from "../../components/TechImage.vue";
import TechTabBar from "../../components/TechTabBar.vue";
import { fetchProductDetail, fetchProducts } from "../../api/shop";
import { deleteCartItem, fetchCart, updateCartItem } from "../../api/trade";
import { formatPrice, hasPrice } from "../../utils/price";
import { getProductContent } from "../../utils/product-content";
import type { ProductDetail, ProductListItem } from "../../types/shop";
import type { CartItem, CartResponse } from "../../types/trade";

const cart = ref<CartResponse | null>(null);
const productSnapshots = ref<Record<number, ProductDetail>>({});
const recommendedProducts = ref<ProductListItem[]>([]);
const selectedItemIds = ref<number[]>([]);
const loading = ref(false);
const pendingItemId = ref<number | null>(null);
const deletingItemId = ref<number | null>(null);
const errorMessage = ref("");

const cartItems = computed(() => cart.value?.items ?? []);
const availableItems = computed(() =>
  cartItems.value.filter((item) => item.is_available),
);
const selectedItems = computed(() =>
  cartItems.value.filter((item) => selectedItemIds.value.includes(item.id)),
);
const hasUnavailableItems = computed(() =>
  cartItems.value.some((item) => !item.is_available),
);
const allSelected = computed(() =>
  availableItems.value.length > 0
  && availableItems.value.every((item) => selectedItemIds.value.includes(item.id)),
);
const selectedTotalAmount = computed(() =>
  selectedItems.value.reduce((total, item) => total + Number(item.subtotal_amount ?? 0), 0),
);
const canCheckout = computed(() => (
  selectedItems.value.length > 0
  && allSelected.value
  && !hasUnavailableItems.value
));

function getSnapshot(item: CartItem): ProductDetail | null {
  return productSnapshots.value[item.product_id] ?? null;
}

function getItemSummary(item: CartItem): string {
  const snapshot = getSnapshot(item);
  if (snapshot) {
    const productContent = getProductContent(snapshot, snapshot.category);
    if (productContent.sellingPoints.length) {
      return productContent.sellingPoints.slice(0, 2).join(" / ");
    }

    if (productContent.subtitle) {
      return productContent.subtitle;
    }
  }

  return item.subtitle || "规格信息待补充";
}

function getItemImages(item: CartItem): string[] {
  const snapshot = getSnapshot(item);
  if (snapshot) {
    const productContent = getProductContent(snapshot, snapshot.category);
    const galleryImages = productContent.galleryImages.filter(Boolean);
    if (galleryImages.length) {
      return galleryImages;
    }
  }

  return [item.cover_image].filter(Boolean);
}

function getItemOriginalPrice(item: CartItem): string | number | null {
  return getSnapshot(item)?.original_price ?? null;
}

function syncSelection(nextCart: CartResponse | null) {
  if (!nextCart) {
    selectedItemIds.value = [];
    return;
  }

  const availableIds = nextCart.items
    .filter((item) => item.is_available)
    .map((item) => item.id);
  const preservedIds = selectedItemIds.value.filter((id) => availableIds.includes(id));

  selectedItemIds.value = preservedIds.length ? preservedIds : availableIds;
}

async function loadProductSnapshots(items: CartItem[]) {
  const productIds = [...new Set(items.map((item) => item.product_id))];
  if (!productIds.length) {
    productSnapshots.value = {};
    return;
  }

  const entries = await Promise.all(productIds.map(async (productId) => {
    try {
      const detail = await fetchProductDetail(productId);
      return [productId, detail] as const;
    } catch {
      return [productId, null] as const;
    }
  }));

  productSnapshots.value = entries.reduce<Record<number, ProductDetail>>((accumulator, entry) => {
    const [productId, detail] = entry;
    if (detail) {
      accumulator[productId] = detail;
    }
    return accumulator;
  }, {});
}

async function loadRecommendations(excludedProductIds: number[]) {
  try {
    const response = await fetchProducts({
      page: 1,
      page_size: 6,
    });

    recommendedProducts.value = response.items
      .filter((item) => !excludedProductIds.includes(item.id))
      .slice(0, 2);
  } catch {
    recommendedProducts.value = [];
  }
}

async function loadCart() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const nextCart = await fetchCart();
    cart.value = nextCart;
    syncSelection(nextCart);
    await Promise.all([
      loadProductSnapshots(nextCart.items),
      loadRecommendations(nextCart.items.map((item) => item.product_id)),
    ]);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "购物车加载失败";
    cart.value = null;
    productSnapshots.value = {};
    recommendedProducts.value = [];
    syncSelection(null);
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
}

function openHomePage() {
  uni.reLaunch({
    url: "/pages/index/index",
  });
}

function openOrderListPage() {
  uni.navigateTo({
    url: "/pages/order/list",
  });
}

function openProductDetail(productId: number) {
  uni.navigateTo({
    url: `/pages/product/detail?id=${productId}`,
  });
}

function toggleItemSelection(item: CartItem) {
  if (!item.is_available) {
    uni.showToast({
      title: item.availability_message || "当前商品暂不可勾选",
      icon: "none",
    });
    return;
  }

  if (selectedItemIds.value.includes(item.id)) {
    selectedItemIds.value = selectedItemIds.value.filter((currentId) => currentId !== item.id);
    return;
  }

  selectedItemIds.value = [...selectedItemIds.value, item.id];
}

function toggleAllSelection() {
  if (!availableItems.value.length) {
    return;
  }

  selectedItemIds.value = allSelected.value
    ? []
    : availableItems.value.map((item) => item.id);
}

async function changeQuantity(item: CartItem, nextQuantity: number) {
  if (pendingItemId.value || nextQuantity <= 0) {
    return;
  }

  pendingItemId.value = item.id;

  try {
    cart.value = await updateCartItem(item.id, { quantity: nextQuantity });
    syncSelection(cart.value);
    await loadProductSnapshots(cart.value?.items ?? []);
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "修改数量失败",
      icon: "none",
    });
  } finally {
    pendingItemId.value = null;
  }
}

async function removeItem(item: CartItem) {
  if (deletingItemId.value) {
    return;
  }

  deletingItemId.value = item.id;

  try {
    await deleteCartItem(item.id);
    uni.showToast({
      title: "已移出购物车",
      icon: "success",
    });
    await loadCart();
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "删除失败",
      icon: "none",
    });
  } finally {
    deletingItemId.value = null;
  }
}

function goConfirmPage() {
  if (!selectedItems.value.length) {
    uni.showToast({
      title: "请先勾选商品",
      icon: "none",
    });
    return;
  }

  if (hasUnavailableItems.value) {
    uni.showToast({
      title: "购物车存在不可下单商品",
      icon: "none",
    });
    return;
  }

  if (!allSelected.value) {
    uni.showToast({
      title: "当前版本仅支持全选购物车后结算",
      icon: "none",
    });
    return;
  }

  uni.navigateTo({
    url: "/pages/order/confirm",
  });
}

onShow(() => {
  void loadCart();
});

onPullDownRefresh(() => {
  void loadCart();
});
</script>

<template>
  <view class="tech-page cart-page">
    <view class="tech-shell">
      <view class="tech-nav cart-nav tech-fade-up">
        <view class="tech-nav__side"></view>

        <view class="tech-nav__center">
          <text class="tech-nav__title">购物车</text>
          <text class="tech-nav__subtitle">NEON CART</text>
        </view>

        <button
          class="tech-icon-button"
          hover-class="tech-button-hover"
          @tap="openOrderListPage"
        >
          订单
        </button>
      </view>

      <view class="tech-panel tech-panel-pad cart-assurance tech-fade-up tech-delay-1">
        <text class="cart-assurance__item">正品保障</text>
        <text class="cart-assurance__item">极速发货</text>
        <text class="cart-assurance__item">7天无理由退换</text>
      </view>

      <view v-if="loading && !cart" class="tech-panel tech-panel-pad tech-state-card tech-fade-up tech-delay-2">
        <text class="tech-state-text">购物车内容加载中...</text>
      </view>

      <view v-else-if="errorMessage && !cart" class="tech-panel tech-panel-pad tech-state-card tech-fade-up tech-delay-2">
        <text class="tech-state-title">购物车加载失败</text>
        <text class="tech-state-text">{{ errorMessage }}</text>
        <button
          class="tech-button tech-button--ghost tech-mini-button retry-button"
          hover-class="tech-button-hover"
          @tap="loadCart"
        >
          重新加载
        </button>
      </view>

      <view v-else-if="!cart || !cart.items.length" class="tech-panel tech-panel-pad tech-state-card tech-fade-up tech-delay-2">
        <text class="tech-state-title">购物车还是空的</text>
        <text class="tech-state-text">先去首页或分类页挑一件商品，再回来完成结算。</text>
        <button
          class="tech-button tech-button--primary tech-mini-button retry-button"
          hover-class="tech-button-hover"
          @tap="openHomePage"
        >
          去逛商品
        </button>
      </view>

      <template v-else>
        <view v-if="hasUnavailableItems" class="tech-panel tech-panel-pad tech-state-card tech-fade-up tech-delay-2">
          <text class="tech-state-title">存在不可下单商品</text>
          <text class="tech-state-text">当前后端结算仍按整个购物车处理，请先删除或调整不可下单商品。</text>
        </view>

        <view class="cart-list">
          <view
            v-for="(item, index) in cart.items"
            :key="item.id"
            class="cart-card tech-stagger-item"
            :style="`animation-delay: ${(index + 1) * 55}ms;`"
          >
            <view
              class="cart-card__selector"
              :class="{
                'cart-card__selector--active': selectedItemIds.includes(item.id),
                'cart-card__selector--disabled': !item.is_available,
              }"
              @tap="toggleItemSelection(item)"
            >
              <view class="cart-card__selector-dot"></view>
            </view>

            <view class="cart-card__main tech-pressable" hover-class="tech-card-hover" @tap="openProductDetail(item.product_id)">
              <TechImage
                :src="getItemImages(item)[0]"
                :sources="getItemImages(item)"
                class="cart-card__image"
                label="购物车商品"
                :sub-label="item.name"
                :show-caption="false"
              />

              <view class="cart-card__body">
                <view class="cart-card__top">
                  <view class="cart-card__copy">
                    <text class="cart-card__title">{{ item.name }}</text>
                    <text class="cart-card__summary">{{ getItemSummary(item) }}</text>
                  </view>

                  <button
                    class="tech-button tech-button--ghost tech-mini-button cart-card__delete"
                    hover-class="tech-button-hover"
                    :loading="deletingItemId === item.id"
                    @tap.stop="removeItem(item)"
                  >
                    删除
                  </button>
                </view>

                <view class="cart-card__price-row">
                  <view>
                    <text class="tech-price cart-card__price">¥{{ formatPrice(item.price) }}</text>
                    <text
                      v-if="hasPrice(getItemOriginalPrice(item))"
                      class="tech-price-original cart-card__original"
                    >
                      ¥{{ formatPrice(getItemOriginalPrice(item)) }}
                    </text>
                  </view>

                  <text v-if="!item.is_available" class="cart-card__warning">
                    {{ item.availability_message || "当前商品暂不可下单" }}
                  </text>
                </view>

                <view class="cart-card__foot">
                  <view class="quantity-stepper">
                    <button
                      class="stepper-button"
                      :disabled="pendingItemId === item.id || item.quantity <= 1"
                      hover-class="tech-button-hover"
                      @tap.stop="changeQuantity(item, item.quantity - 1)"
                    >
                      -
                    </button>
                    <text class="quantity-text">{{ item.quantity }}</text>
                    <button
                      class="stepper-button"
                      :disabled="pendingItemId === item.id || !item.is_available || item.quantity >= item.stock"
                      hover-class="tech-button-hover"
                      @tap.stop="changeQuantity(item, item.quantity + 1)"
                    >
                      +
                    </button>
                  </view>

                  <text class="cart-card__subtotal">小计 ¥{{ formatPrice(item.subtotal_amount) }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>

        <view v-if="recommendedProducts.length" class="tech-panel tech-panel-pad cart-recommend tech-fade-up tech-delay-4">
          <view class="cart-recommend__head">
            <view>
              <text class="tech-kicker">为你推荐</text>
              <text class="cart-recommend__title">优先级低于购物车主内容</text>
            </view>
          </view>

          <view class="cart-recommend__grid">
            <ProductCard
              v-for="(product, index) in recommendedProducts"
              :key="product.id"
              :product="product"
              variant="compact"
              :stagger-index="index + 1"
              label="推荐商品"
              action-label="查看"
              @select="openProductDetail"
            />
          </view>
        </view>
      </template>
    </view>

    <view v-if="cart && cart.items.length" class="cart-action-bar">
      <view class="cart-action-bar__select" @tap="toggleAllSelection">
        <view
          class="cart-card__selector"
          :class="{ 'cart-card__selector--active': allSelected }"
        >
          <view class="cart-card__selector-dot"></view>
        </view>
        <text class="cart-action-bar__label">全选</text>
      </view>

      <view class="cart-action-bar__summary">
        <text class="cart-action-bar__caption">合计</text>
        <text class="tech-price cart-action-bar__price">¥{{ formatPrice(selectedTotalAmount) }}</text>
        <text class="cart-action-bar__note">当前版本按整车结算</text>
      </view>

      <button
        class="tech-button tech-button--primary cart-action-bar__button"
        hover-class="tech-button-hover"
        :disabled="!canCheckout"
        @tap="goConfirmPage"
      >
        去结算
      </button>
    </view>

    <TechTabBar active="cart" />
  </view>
</template>

<style scoped>
.cart-page {
  padding-bottom: 196rpx;
}

.cart-assurance {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.cart-assurance__item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 60rpx;
  border-radius: 22rpx;
  background: rgba(102, 87, 255, 0.1);
  color: #d7d8ff;
  font-size: 22rpx;
  font-weight: 600;
}

.cart-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.cart-card {
  display: flex;
  align-items: stretch;
  gap: 16rpx;
}

.cart-card__selector {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48rpx;
  min-width: 48rpx;
  height: 48rpx;
  margin-top: 118rpx;
  border: 1rpx solid rgba(184, 173, 255, 0.18);
  border-radius: 50%;
  background: rgba(14, 17, 36, 0.84);
}

.cart-card__selector--active {
  background: linear-gradient(135deg, rgba(104, 87, 255, 0.94), rgba(53, 190, 255, 0.92));
}

.cart-card__selector--disabled {
  opacity: 0.42;
}

.cart-card__selector-dot {
  width: 18rpx;
  height: 18rpx;
  border-radius: 50%;
  background: #f7f9ff;
  opacity: 0;
}

.cart-card__selector--active .cart-card__selector-dot {
  opacity: 1;
}

.cart-card__main {
  display: flex;
  flex: 1;
  gap: 18rpx;
  padding: 18rpx;
  border: 1rpx solid rgba(176, 168, 255, 0.14);
  border-radius: 32rpx;
  background:
    linear-gradient(180deg, rgba(21, 18, 46, 0.84), rgba(9, 14, 29, 0.9));
}

.cart-card__image {
  width: 236rpx;
  min-width: 236rpx;
  height: 236rpx;
  border-radius: 26rpx;
}

.cart-card__body {
  flex: 1;
}

.cart-card__top,
.cart-card__price-row,
.cart-card__foot {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.cart-card__copy {
  flex: 1;
}

.cart-card__title {
  display: block;
  color: var(--tech-text-primary);
  font-size: 30rpx;
  font-weight: 700;
  line-height: 1.36;
}

.cart-card__summary {
  display: block;
  margin-top: 12rpx;
  color: var(--tech-text-secondary);
  font-size: 24rpx;
  line-height: 1.72;
}

.cart-card__delete {
  min-width: 112rpx;
}

.cart-card__price-row {
  margin-top: 18rpx;
}

.cart-card__price {
  display: block;
  font-size: 40rpx;
}

.cart-card__original {
  display: block;
  margin-top: 10rpx;
}

.cart-card__warning {
  max-width: 220rpx;
  color: #ffb4c8;
  font-size: 22rpx;
  line-height: 1.64;
}

.cart-card__foot {
  align-items: center;
  margin-top: 24rpx;
}

.cart-card__subtotal {
  color: var(--tech-text-secondary);
  font-size: 24rpx;
}

.quantity-stepper {
  display: inline-flex;
  align-items: center;
  padding: 8rpx;
  border: 1rpx solid rgba(184, 173, 255, 0.14);
  border-radius: 999rpx;
  background: rgba(12, 16, 32, 0.88);
}

.stepper-button {
  width: 54rpx;
  height: 54rpx;
  padding: 0;
  border: none;
  border-radius: 999rpx;
  background: rgba(23, 29, 61, 0.92);
  color: var(--tech-text-primary);
  font-size: 34rpx;
  line-height: 54rpx;
}

.quantity-text {
  min-width: 56rpx;
  text-align: center;
  color: var(--tech-text-primary);
  font-size: 28rpx;
  font-weight: 700;
}

.cart-recommend__title {
  display: block;
  margin-top: 14rpx;
  color: var(--tech-text-primary);
  font-size: 34rpx;
  font-weight: 700;
}

.cart-recommend__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
  margin-top: 24rpx;
}

.retry-button {
  margin-top: 18rpx;
}

.cart-action-bar {
  position: fixed;
  right: 18rpx;
  bottom: calc(128rpx + env(safe-area-inset-bottom));
  left: 18rpx;
  z-index: 18;
  display: grid;
  grid-template-columns: 146rpx 1fr 214rpx;
  gap: 12rpx;
  align-items: center;
  padding: 12rpx 16rpx;
  border: 1rpx solid rgba(184, 173, 255, 0.16);
  border-radius: 999rpx;
  background:
    linear-gradient(135deg, rgba(22, 18, 48, 0.94), rgba(8, 13, 28, 0.94));
  box-shadow: 0 18rpx 40rpx rgba(0, 0, 0, 0.28);
  backdrop-filter: blur(24rpx);
}

.cart-action-bar__select {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.cart-action-bar__label,
.cart-action-bar__caption {
  color: var(--tech-text-secondary);
  font-size: 24rpx;
}

.cart-action-bar__summary {
  min-width: 0;
}

.cart-action-bar__price {
  display: block;
  margin-top: 8rpx;
  font-size: 40rpx;
}

.cart-action-bar__note {
  display: block;
  margin-top: 6rpx;
  color: var(--tech-text-tertiary);
  font-size: 20rpx;
  line-height: 1.5;
}

@media (max-width: 520px) {
  .cart-assurance,
  .cart-card__main,
  .cart-recommend__grid,
  .cart-action-bar {
    grid-template-columns: 1fr;
  }

  .cart-card {
    flex-direction: column;
  }

  .cart-card__selector {
    margin-top: 0;
  }

  .cart-card__main,
  .cart-card__top,
  .cart-card__price-row,
  .cart-card__foot,
  .cart-action-bar__select {
    flex-direction: column;
    align-items: flex-start;
  }

  .cart-card__image,
  .cart-action-bar__button {
    width: 100%;
  }
}
</style>

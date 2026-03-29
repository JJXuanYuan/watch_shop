<script setup lang="ts">
import { computed } from "vue";

interface Props {
  modelValue?: string;
  placeholder?: string;
  actionLabel?: string;
  readonly?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: "",
  placeholder: "搜索商品",
  actionLabel: "搜索",
  readonly: false,
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
  submit: [value: string];
  focus: [];
}>();

const displayValue = computed(() => props.modelValue.trim());

function handleInput(event: Record<string, unknown>) {
  const detail = (event.detail ?? {}) as { value?: string };
  emit("update:modelValue", detail.value ?? "");
}

function handleSubmit() {
  emit("submit", displayValue.value);
}

function handleFocus() {
  emit("focus");
}
</script>

<template>
  <view class="tech-search">
    <view class="tech-search__icon" aria-hidden="true">
      <view class="tech-search__icon-circle"></view>
      <view class="tech-search__icon-tail"></view>
    </view>

    <input
      class="tech-search__input"
      :value="modelValue"
      :placeholder="placeholder"
      confirm-type="search"
      :disabled="readonly"
      @input="handleInput"
      @confirm="handleSubmit"
      @focus="handleFocus"
    />

    <button
      class="tech-search__action"
      hover-class="tech-button-hover"
      @tap="handleSubmit"
    >
      {{ actionLabel }}
    </button>
  </view>
</template>

<style scoped>
.tech-search {
  display: flex;
  align-items: center;
  gap: 18rpx;
  min-height: 92rpx;
  padding: 12rpx 14rpx 12rpx 22rpx;
  border: 1rpx solid rgba(175, 159, 255, 0.16);
  border-radius: 999rpx;
  background:
    linear-gradient(135deg, rgba(35, 24, 66, 0.86), rgba(12, 18, 36, 0.9)),
    rgba(10, 14, 30, 0.88);
  box-shadow:
    inset 0 1rpx 0 rgba(255, 255, 255, 0.04),
    0 16rpx 38rpx rgba(4, 7, 22, 0.24);
  backdrop-filter: blur(18rpx);
}

.tech-search__icon {
  position: relative;
  width: 34rpx;
  min-width: 34rpx;
  height: 34rpx;
}

.tech-search__icon-circle {
  width: 24rpx;
  height: 24rpx;
  border: 3rpx solid rgba(213, 219, 255, 0.82);
  border-radius: 50%;
}

.tech-search__icon-tail {
  position: absolute;
  right: 1rpx;
  bottom: 2rpx;
  width: 10rpx;
  height: 3rpx;
  border-radius: 999rpx;
  background: rgba(213, 219, 255, 0.82);
  transform: rotate(44deg);
  transform-origin: right center;
}

.tech-search__input {
  flex: 1;
  min-width: 0;
  height: 64rpx;
  color: var(--tech-text-primary);
  font-size: 27rpx;
}

.tech-search__action {
  min-width: 128rpx;
  height: 64rpx;
  margin: 0;
  padding: 0 22rpx;
  border: none;
  border-radius: 999rpx;
  background: linear-gradient(135deg, rgba(110, 100, 255, 0.92), rgba(74, 208, 255, 0.92));
  color: #eff3ff;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 64rpx;
  box-shadow: 0 12rpx 24rpx rgba(76, 90, 255, 0.24);
}
</style>

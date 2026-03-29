<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

interface Props {
  src?: string | null;
  sources?: Array<string | null | undefined>;
  mode?: UniHelper.ImageMode;
  label?: string;
  subLabel?: string;
  showCaption?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  src: "",
  sources: () => [],
  mode: "aspectFill",
  label: "商品主图",
  subLabel: "影像加载中",
  showCaption: false,
});

const failed = ref(false);
const showSheen = ref(false);
const currentSourceIndex = ref(0);
let sheenTimer: ReturnType<typeof setTimeout> | null = null;

const sourceQueue = computed(() => {
  const rawSources = props.sources.length ? props.sources : [props.src];
  const uniqueSources: string[] = [];

  rawSources.forEach((item) => {
    const normalizedItem = typeof item === "string" ? item.trim() : "";
    if (!normalizedItem || uniqueSources.includes(normalizedItem)) {
      return;
    }

    uniqueSources.push(normalizedItem);
  });

  return uniqueSources;
});

const displaySrc = computed(() => {
  if (failed.value) {
    return "";
  }

  return sourceQueue.value[currentSourceIndex.value] || "";
});

function resetImageState() {
  failed.value = false;
  currentSourceIndex.value = 0;
  triggerSheen();
}

function triggerSheen() {
  showSheen.value = true;

  if (sheenTimer) {
    clearTimeout(sheenTimer);
  }

  sheenTimer = setTimeout(() => {
    showSheen.value = false;
  }, 950);
}

watch(
  sourceQueue,
  () => {
    resetImageState();
  },
  { deep: true },
);

function handleError() {
  if (currentSourceIndex.value < sourceQueue.value.length - 1) {
    currentSourceIndex.value += 1;
    triggerSheen();
    return;
  }

  failed.value = true;
}

onMounted(() => {
  resetImageState();
});

onUnmounted(() => {
  if (sheenTimer) {
    clearTimeout(sheenTimer);
  }
});
</script>

<template>
  <view
    class="tech-image-shell"
    :class="{ 'tech-image-shell--sheen': showSheen }"
  >
    <image
      v-if="displaySrc"
      :src="displaySrc"
      :mode="mode"
      class="tech-image-media"
      @error="handleError"
    />

    <view v-else class="tech-image-placeholder">
      <view class="tech-image-silhouette">
        <view class="tech-image-silhouette__strap"></view>
        <view class="tech-image-silhouette__case"></view>
        <view class="tech-image-silhouette__dial"></view>
      </view>
      <view class="tech-image-copy">
        <text class="tech-image-label">{{ label }}</text>
        <text class="tech-image-sub">{{ subLabel }}</text>
      </view>
    </view>

    <view class="tech-image-vignette"></view>

    <view v-if="showCaption" class="tech-image-overlay">
      <view class="tech-image-caption">
        <text class="tech-image-label">{{ label }}</text>
        <text class="tech-image-sub">{{ displaySrc ? subLabel : "正在准备展示图" }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.tech-image-shell {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: inherit;
  background:
    radial-gradient(circle at 18% 0%, rgba(115, 217, 255, 0.12), transparent 34%),
    linear-gradient(180deg, rgba(17, 25, 41, 0.96), rgba(8, 12, 22, 0.98));
}

.tech-image-shell::before {
  content: "";
  position: absolute;
  inset: -18%;
  background: linear-gradient(110deg, transparent 32%, rgba(255, 255, 255, 0.12) 48%, transparent 64%);
  transform: translateX(-140%);
  opacity: 0;
  pointer-events: none;
}

.tech-image-shell--sheen::before,
.tech-image-shell:active::before {
  opacity: 1;
  animation: tech-image-sheen 0.85s ease-out forwards;
}

.tech-image-media,
.tech-image-placeholder {
  width: 100%;
  height: 100%;
}

.tech-image-media {
  display: block;
}

.tech-image-placeholder {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28rpx;
}

.tech-image-silhouette {
  position: relative;
  width: 44%;
  height: 44%;
  min-width: 134rpx;
  min-height: 134rpx;
  opacity: 0.62;
}

.tech-image-silhouette__strap,
.tech-image-silhouette__case,
.tech-image-silhouette__dial {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.tech-image-silhouette__strap {
  top: 0;
  width: 40%;
  height: 100%;
  border-radius: 999rpx;
  background: linear-gradient(180deg, rgba(84, 101, 133, 0.16), rgba(84, 101, 133, 0.04));
}

.tech-image-silhouette__case {
  top: 21%;
  width: 66%;
  height: 58%;
  border-radius: 38rpx;
  background: linear-gradient(180deg, rgba(130, 158, 209, 0.22), rgba(130, 158, 209, 0.08));
  box-shadow: inset 0 0 0 1rpx rgba(255, 255, 255, 0.06);
}

.tech-image-silhouette__dial {
  top: 29%;
  width: 42%;
  height: 42%;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, rgba(115, 217, 255, 0.26), rgba(115, 217, 255, 0.04));
  box-shadow: 0 0 32rpx rgba(115, 217, 255, 0.08);
}

.tech-image-copy {
  position: absolute;
  right: 28rpx;
  bottom: 28rpx;
  left: 28rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  padding: 18rpx 20rpx;
  border: 1rpx solid rgba(170, 195, 255, 0.1);
  border-radius: 24rpx;
  background: rgba(6, 12, 21, 0.56);
  backdrop-filter: blur(16rpx);
}

.tech-image-vignette {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(3, 7, 12, 0.02), rgba(3, 7, 12, 0.32)),
    linear-gradient(0deg, rgba(3, 7, 12, 0.22), transparent 42%);
  pointer-events: none;
}

.tech-image-overlay {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  padding: 22rpx 22rpx 20rpx;
  pointer-events: none;
}

.tech-image-caption {
  display: inline-flex;
  flex-direction: column;
  gap: 8rpx;
  max-width: 82%;
  padding: 12rpx 16rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.08);
  border-radius: 22rpx;
  background: rgba(7, 12, 21, 0.3);
  backdrop-filter: blur(14rpx);
}

.tech-image-label {
  color: #f7f9ff;
  font-size: 18rpx;
  font-weight: 600;
  letter-spacing: 2rpx;
}

.tech-image-sub {
  color: rgba(177, 189, 212, 0.82);
  font-size: 20rpx;
  line-height: 1.52;
}

@keyframes tech-image-sheen {
  from {
    transform: translateX(-140%);
  }

  to {
    transform: translateX(140%);
  }
}
</style>

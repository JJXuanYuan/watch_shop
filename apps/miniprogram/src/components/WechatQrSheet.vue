<script setup lang="ts">
import { computed } from "vue";

interface Props {
  modelValue: boolean;
  title?: string;
  description?: string;
}

const props = withDefaults(defineProps<Props>(), {
  title: "微信二维码",
  description: "此处为前端弹层占位，请替换为真实微信二维码素材。",
});

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
}>();

function isFinderZone(row: number, column: number): boolean {
  const inTopLeft = row <= 6 && column <= 6;
  const inTopRight = row <= 6 && column >= 14;
  const inBottomLeft = row >= 14 && column <= 6;
  return inTopLeft || inTopRight || inBottomLeft;
}

function isFinderFill(row: number, column: number): boolean {
  const zones = [
    { rowStart: 0, rowEnd: 6, colStart: 0, colEnd: 6 },
    { rowStart: 0, rowEnd: 6, colStart: 14, colEnd: 20 },
    { rowStart: 14, rowEnd: 20, colStart: 0, colEnd: 6 },
  ];

  const matchedZone = zones.find((zone) => (
    row >= zone.rowStart
    && row <= zone.rowEnd
    && column >= zone.colStart
    && column <= zone.colEnd
  ));

  if (!matchedZone) {
    return false;
  }

  const normalizedRow = row - matchedZone.rowStart;
  const normalizedColumn = column - matchedZone.colStart;
  const onBorder =
    normalizedRow === 0
    || normalizedRow === 6
    || normalizedColumn === 0
    || normalizedColumn === 6;
  const onCore =
    normalizedRow >= 2
    && normalizedRow <= 4
    && normalizedColumn >= 2
    && normalizedColumn <= 4;

  return onBorder || onCore;
}

const qrCells = computed(() => {
  const size = 21;
  const cells: boolean[] = [];

  for (let row = 0; row < size; row += 1) {
    for (let column = 0; column < size; column += 1) {
      if (isFinderZone(row, column)) {
        cells.push(isFinderFill(row, column));
        continue;
      }

      const seededValue = (row * 17 + column * 13 + row * column) % 7;
      const diagonalPulse = (row + column) % 5 === 0;
      cells.push(seededValue <= 2 || diagonalPulse);
    }
  }

  return cells;
});

function closeSheet() {
  emit("update:modelValue", false);
}
</script>

<template>
  <view v-if="modelValue" class="wechat-sheet" @tap="closeSheet">
    <view class="wechat-sheet__mask"></view>

    <view class="wechat-sheet__panel tech-panel tech-panel-pad" @tap.stop>
      <view class="wechat-sheet__head">
        <view>
          <text class="tech-kicker">联系入口</text>
          <text class="wechat-sheet__title">{{ title }}</text>
        </view>

        <button
          class="tech-button tech-button--ghost tech-mini-button"
          hover-class="tech-button-hover"
          @tap="closeSheet"
        >
          关闭
        </button>
      </view>

      <view class="wechat-sheet__qr-shell">
        <view class="wechat-sheet__qr">
          <view
            v-for="(filled, index) in qrCells"
            :key="index"
            class="wechat-sheet__qr-cell"
            :class="{ 'wechat-sheet__qr-cell--filled': filled }"
          ></view>
        </view>
      </view>

      <text class="wechat-sheet__description">{{ description }}</text>
      <text class="wechat-sheet__note">当前弹层和交互已完成，后续只需替换成真实二维码图片即可。</text>
    </view>
  </view>
</template>

<style scoped>
.wechat-sheet {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 24rpx;
}

.wechat-sheet__mask {
  position: absolute;
  inset: 0;
  background: rgba(2, 5, 16, 0.72);
  backdrop-filter: blur(14rpx);
}

.wechat-sheet__panel {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 680rpx;
  border-radius: 38rpx;
}

.wechat-sheet__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.wechat-sheet__title {
  display: block;
  margin-top: 14rpx;
  color: var(--tech-text-primary);
  font-size: 38rpx;
  font-weight: 700;
}

.wechat-sheet__qr-shell {
  display: flex;
  justify-content: center;
  margin-top: 26rpx;
}

.wechat-sheet__qr {
  display: grid;
  grid-template-columns: repeat(21, 1fr);
  gap: 6rpx;
  width: 420rpx;
  height: 420rpx;
  padding: 22rpx;
  border: 1rpx solid rgba(178, 180, 255, 0.18);
  border-radius: 32rpx;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(230, 235, 255, 0.98));
  box-shadow:
    inset 0 0 0 1rpx rgba(255, 255, 255, 0.42),
    0 18rpx 38rpx rgba(6, 10, 30, 0.18);
}

.wechat-sheet__qr-cell {
  border-radius: 4rpx;
  background: rgba(18, 26, 48, 0.06);
}

.wechat-sheet__qr-cell--filled {
  background: #121722;
}

.wechat-sheet__description,
.wechat-sheet__note {
  display: block;
  margin-top: 20rpx;
  color: var(--tech-text-secondary);
  font-size: 24rpx;
  line-height: 1.72;
  text-align: center;
}

.wechat-sheet__note {
  color: var(--tech-text-tertiary);
}
</style>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import { createAddress, fetchAddresses, updateAddress } from "../../api/address";
import type { AddressPayload, UserAddress } from "../../types/address";

const SELECTED_ADDRESS_STORAGE_KEY = "watch_shop_selected_address_id";

interface AddressFormQuery {
  id?: string;
}

const loading = ref(false);
const saving = ref(false);
const editingAddressId = ref<number | null>(null);

const form = reactive<AddressPayload>({
  receiver_name: "",
  receiver_phone: "",
  province: "",
  city: "",
  district: "",
  detail_address: "",
  is_default: false,
});

function parseNumber(value?: string): number | null {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) && numericValue > 0 ? numericValue : null;
}

function applyAddress(address: UserAddress) {
  form.receiver_name = address.receiver_name;
  form.receiver_phone = address.receiver_phone;
  form.province = address.province;
  form.city = address.city;
  form.district = address.district;
  form.detail_address = address.detail_address;
  form.is_default = address.is_default;
}

function validateForm(): string | null {
  if (!form.receiver_name.trim()) {
    return "请填写收件人";
  }
  if (!/^1\d{10}$/.test(form.receiver_phone.trim())) {
    return "请输入正确的手机号";
  }
  if (!form.province.trim() || !form.city.trim() || !form.district.trim()) {
    return "请补全省市区";
  }
  if (!form.detail_address.trim()) {
    return "请填写详细地址";
  }
  return null;
}

async function loadEditingAddress(addressId: number) {
  loading.value = true;

  try {
    const response = await fetchAddresses();
    const address = response.items.find((item) => item.id === addressId);
    if (!address) {
      throw new Error("地址不存在");
    }
    applyAddress(address);
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "地址加载失败",
      icon: "none",
    });
  } finally {
    loading.value = false;
  }
}

async function handleSubmit() {
  if (saving.value) {
    return;
  }

  const validationMessage = validateForm();
  if (validationMessage) {
    uni.showToast({
      title: validationMessage,
      icon: "none",
    });
    return;
  }

  saving.value = true;

  try {
    const payload: AddressPayload = {
      receiver_name: form.receiver_name.trim(),
      receiver_phone: form.receiver_phone.trim(),
      province: form.province.trim(),
      city: form.city.trim(),
      district: form.district.trim(),
      detail_address: form.detail_address.trim(),
      is_default: form.is_default,
    };

    const address = editingAddressId.value
      ? await updateAddress(editingAddressId.value, payload)
      : await createAddress(payload);

    uni.setStorageSync(SELECTED_ADDRESS_STORAGE_KEY, address.id);
    uni.showToast({
      title: editingAddressId.value ? "地址已更新" : "地址已新增",
      icon: "success",
    });
    setTimeout(() => {
      uni.navigateBack();
    }, 300);
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "保存地址失败",
      icon: "none",
    });
  } finally {
    saving.value = false;
  }
}

onLoad((query) => {
  const pageQuery = (query ?? {}) as AddressFormQuery;
  editingAddressId.value = parseNumber(pageQuery.id);
  uni.setNavigationBarTitle({
    title: editingAddressId.value ? "编辑地址" : "新增地址",
  });

  if (editingAddressId.value) {
    void loadEditingAddress(editingAddressId.value);
  }
});
</script>

<template>
  <view class="page">
    <view class="form-card">
      <text class="form-kicker">Address Form</text>
      <text class="form-title">{{ editingAddressId ? "编辑地址" : "新增地址" }}</text>
      <text class="form-summary">当前只做最小可用地址体系，先满足下单快照与履约展示链路。</text>

      <view v-if="loading" class="loading-state">
        <text class="loading-text">地址信息加载中...</text>
      </view>

      <view v-else class="form-shell">
        <view class="field">
          <text class="field-label">收件人</text>
          <input v-model="form.receiver_name" class="field-input" placeholder="请输入收件人姓名" />
        </view>

        <view class="field">
          <text class="field-label">手机号</text>
          <input
            v-model="form.receiver_phone"
            class="field-input"
            type="number"
            maxlength="11"
            placeholder="请输入 11 位手机号"
          />
        </view>

        <view class="field">
          <text class="field-label">省份</text>
          <input v-model="form.province" class="field-input" placeholder="例如：上海市" />
        </view>

        <view class="field">
          <text class="field-label">城市</text>
          <input v-model="form.city" class="field-input" placeholder="例如：上海市" />
        </view>

        <view class="field">
          <text class="field-label">区县</text>
          <input v-model="form.district" class="field-input" placeholder="例如：静安区" />
        </view>

        <view class="field">
          <text class="field-label">详细地址</text>
          <textarea
            v-model="form.detail_address"
            class="field-textarea"
            maxlength="255"
            placeholder="请输入街道门牌、楼栋房间等详细地址"
          />
        </view>

        <label class="switch-row">
          <switch
            :checked="form.is_default"
            color="#9a712d"
            @change="form.is_default = $event.detail.value"
          />
          <text class="switch-text">设为默认地址</text>
        </label>
      </view>
    </view>

    <view class="footer-action">
      <button class="submit-button" :loading="saving" @tap="handleSubmit">保存地址</button>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx 24rpx 48rpx;
  color: #2f2619;
}

.form-card {
  padding: 30rpx 28rpx;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18rpx 48rpx rgba(84, 62, 23, 0.08);
}

.form-kicker {
  display: block;
  color: #8d6c2f;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
  text-transform: uppercase;
}

.form-title {
  display: block;
  margin-top: 14rpx;
  font-size: 42rpx;
  font-weight: 700;
}

.form-summary,
.loading-text {
  display: block;
  margin-top: 12rpx;
  color: #665946;
  font-size: 26rpx;
  line-height: 1.7;
}

.form-shell,
.footer-action,
.loading-state {
  margin-top: 24rpx;
}

.field + .field {
  margin-top: 18rpx;
}

.field-label {
  display: block;
  margin-bottom: 10rpx;
  color: #665946;
  font-size: 24rpx;
  font-weight: 700;
}

.field-input,
.field-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 24rpx 22rpx;
  border-radius: 22rpx;
  background: #fbf8f3;
  color: #20180d;
  font-size: 28rpx;
}

.field-textarea {
  min-height: 200rpx;
}

.switch-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 24rpx;
}

.switch-text {
  font-size: 26rpx;
  color: #4f4333;
}

.submit-button {
  height: 84rpx;
  border: none;
  border-radius: 999rpx;
  background: #2c2114;
  color: #fff7e8;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 84rpx;
}
</style>

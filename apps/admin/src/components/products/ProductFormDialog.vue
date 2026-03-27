<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";

import { createAdminProduct, updateAdminProduct } from "../../api/products";
import { uploadAdminImage } from "../../api/uploads";
import type {
  AdminCategoryItem,
  AdminProductPayload,
  AdminProductResponse,
  ProductStatus,
} from "../../types/admin";

interface ProductFormState {
  name: string;
  subtitle: string;
  category_id?: number;
  price: number;
  original_price?: number;
  stock: number;
  sales: number;
  status: ProductStatus;
  cover_image: string;
  banner_images: string[];
  detail_content: string;
  sort_order: number;
  is_featured: boolean;
}

const props = defineProps<{
  modelValue: boolean;
  mode: "create" | "edit";
  categories: AdminCategoryItem[];
  product: AdminProductResponse | null;
  loading?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  submitted: [];
}>();

const formRef = ref<FormInstance>();
const coverInputRef = ref<HTMLInputElement | null>(null);
const bannerInputRef = ref<HTMLInputElement | null>(null);
const submitting = ref(false);
const uploadingCover = ref(false);
const uploadingBanner = ref(false);
const manualBannerUrl = ref("");

const formState = reactive<ProductFormState>({
  name: "",
  subtitle: "",
  category_id: undefined,
  price: 0,
  original_price: undefined,
  stock: 0,
  sales: 0,
  status: "draft",
  cover_image: "",
  banner_images: [],
  detail_content: "",
  sort_order: 0,
  is_featured: false,
});

const rules: FormRules<ProductFormState> = {
  name: [
    {
      required: true,
      message: "请输入商品名称",
      trigger: "blur",
    },
  ],
  category_id: [
    {
      required: true,
      message: "请选择商品分类",
      trigger: "change",
    },
  ],
  price: [
    {
      required: true,
      message: "请输入售价",
      trigger: "change",
    },
    {
      validator: (_rule, value, callback) => {
        if (typeof value !== "number" || value <= 0) {
          callback(new Error("售价必须大于 0"));
          return;
        }

        callback();
      },
      trigger: "change",
    },
  ],
  original_price: [
    {
      validator: (_rule, value, callback) => {
        if (value === undefined || value === null || value === 0) {
          callback();
          return;
        }

        if (typeof value !== "number" || value < formState.price) {
          callback(new Error("划线价不能小于售价"));
          return;
        }

        callback();
      },
      trigger: "change",
    },
  ],
  cover_image: [
    {
      required: true,
      message: "请上传或填写主图 URL",
      trigger: "blur",
    },
  ],
};

function normalizeBannerImages(images: string[]): string[] {
  return images.map((item) => item.trim()).filter(Boolean);
}

function resetFileSelection(inputRef: typeof coverInputRef) {
  if (inputRef.value) {
    inputRef.value.value = "";
  }
}

function resetForm() {
  formState.name = "";
  formState.subtitle = "";
  formState.category_id = props.categories[0]?.id;
  formState.price = 0;
  formState.original_price = undefined;
  formState.stock = 0;
  formState.sales = 0;
  formState.status = "draft";
  formState.cover_image = "";
  formState.banner_images = [];
  formState.detail_content = "";
  formState.sort_order = 0;
  formState.is_featured = false;
  manualBannerUrl.value = "";
}

function applyProduct(product: AdminProductResponse | null) {
  if (!product) {
    resetForm();
    return;
  }

  formState.name = product.name;
  formState.subtitle = product.subtitle ?? "";
  formState.category_id = product.category_id;
  formState.price = Number(product.price);
  formState.original_price =
    product.original_price === null ? undefined : Number(product.original_price);
  formState.stock = product.stock;
  formState.sales = product.sales;
  formState.status = product.status;
  formState.cover_image = product.cover_image;
  formState.banner_images = [...product.banner_images];
  formState.detail_content = product.detail_content ?? "";
  formState.sort_order = product.sort_order;
  formState.is_featured = product.is_featured;
  manualBannerUrl.value = "";
}

function closeDialog() {
  emit("update:modelValue", false);
}

function openCoverPicker() {
  coverInputRef.value?.click();
}

function openBannerPicker() {
  bannerInputRef.value?.click();
}

function addManualBannerImage() {
  const imageUrl = manualBannerUrl.value.trim();
  if (!imageUrl) {
    ElMessage.warning("请输入轮播图 URL");
    return;
  }

  formState.banner_images.push(imageUrl);
  manualBannerUrl.value = "";
}

function addEmptyBannerImage() {
  formState.banner_images.push("");
}

function removeBannerImage(index: number) {
  formState.banner_images.splice(index, 1);
}

function moveBannerImage(index: number, step: -1 | 1) {
  const targetIndex = index + step;
  if (targetIndex < 0 || targetIndex >= formState.banner_images.length) {
    return;
  }

  const [currentImage] = formState.banner_images.splice(index, 1);
  formState.banner_images.splice(targetIndex, 0, currentImage);
}

async function handleCoverFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) {
    return;
  }

  uploadingCover.value = true;

  try {
    const result = await uploadAdminImage(file);
    formState.cover_image = result.url;
    ElMessage.success("主图上传成功");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "主图上传失败");
  } finally {
    uploadingCover.value = false;
    resetFileSelection(coverInputRef);
  }
}

async function handleBannerFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files ?? []);
  if (!files.length) {
    return;
  }

  uploadingBanner.value = true;
  let successCount = 0;
  let failureMessage: string | null = null;

  try {
    for (const file of files) {
      try {
        const result = await uploadAdminImage(file);
        formState.banner_images.push(result.url);
        successCount += 1;
      } catch (error) {
        failureMessage = error instanceof Error ? error.message : "轮播图上传失败";
        break;
      }
    }

    if (successCount > 0) {
      ElMessage.success(`已上传 ${successCount} 张轮播图`);
    }

    if (failureMessage) {
      ElMessage.error(failureMessage);
    }
  } finally {
    uploadingBanner.value = false;
    resetFileSelection(bannerInputRef);
  }
}

function buildPayload(): AdminProductPayload {
  return {
    name: formState.name.trim(),
    subtitle: formState.subtitle.trim() || null,
    category_id: Number(formState.category_id),
    price: formState.price,
    original_price:
      formState.original_price === undefined || formState.original_price === null
        ? null
        : formState.original_price,
    stock: formState.stock,
    sales: formState.sales,
    status: formState.status,
    cover_image: formState.cover_image.trim(),
    banner_images: normalizeBannerImages(formState.banner_images),
    detail_content: formState.detail_content.trim() || null,
    sort_order: formState.sort_order,
    is_featured: formState.is_featured,
  };
}

async function handleSubmit() {
  const form = formRef.value;
  if (!form) {
    return;
  }

  const isValid = await form.validate().catch(() => false);
  if (!isValid) {
    return;
  }

  submitting.value = true;

  try {
    const payload = buildPayload();

    if (props.mode === "create") {
      await createAdminProduct(payload);
      ElMessage.success("商品创建成功");
    } else {
      if (!props.product) {
        throw new Error("缺少商品详情，无法编辑");
      }

      await updateAdminProduct(props.product.id, payload);
      ElMessage.success("商品更新成功");
    }

    emit("submitted");
    closeDialog();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "商品提交失败");
  } finally {
    submitting.value = false;
  }
}

watch(
  () => props.modelValue,
  (visible) => {
    if (!visible) {
      return;
    }

    applyProduct(props.product);
    formRef.value?.clearValidate();
  },
);

watch(
  () => props.product,
  (product) => {
    if (!props.modelValue) {
      return;
    }

    applyProduct(product);
  },
);

watch(
  () => props.categories,
  (categories) => {
    if (!formState.category_id && categories.length && props.mode === "create") {
      formState.category_id = categories[0].id;
    }
  },
  { immediate: true },
);
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    :title="mode === 'create' ? '新增商品' : '编辑商品'"
    width="920px"
    destroy-on-close
    :close-on-click-modal="false"
    @close="closeDialog"
  >
    <input
      ref="coverInputRef"
      class="hidden-file-input"
      type="file"
      accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
      @change="handleCoverFileChange"
    />
    <input
      ref="bannerInputRef"
      class="hidden-file-input"
      type="file"
      accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
      multiple
      @change="handleBannerFileChange"
    />

    <el-skeleton :loading="Boolean(loading)" animated>
      <template #template>
        <el-skeleton-item variant="text" style="width: 100%; height: 28px;" />
        <el-skeleton-item variant="text" style="width: 100%; height: 320px; margin-top: 18px;" />
      </template>

      <el-form
        ref="formRef"
        label-position="top"
        :model="formState"
        :rules="rules"
      >
        <div class="form-grid">
          <el-form-item label="商品名称" prop="name">
            <el-input v-model="formState.name" placeholder="请输入商品名称" />
          </el-form-item>

          <el-form-item label="副标题">
            <el-input v-model="formState.subtitle" placeholder="请输入副标题" />
          </el-form-item>

          <el-form-item label="商品分类" prop="category_id">
            <el-select
              v-model="formState.category_id"
              placeholder="请选择分类"
              filterable
            >
              <el-option
                v-for="category in categories"
                :key="category.id"
                :label="`${category.name}（${category.status === 'enabled' ? '启用' : '禁用'}）`"
                :value="category.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="状态">
            <el-select v-model="formState.status">
              <el-option label="草稿" value="draft" />
              <el-option label="上架中" value="on_sale" />
              <el-option label="已下架" value="off_sale" />
            </el-select>
          </el-form-item>

          <el-form-item label="售价" prop="price">
            <el-input-number
              v-model="formState.price"
              :min="0"
              :precision="2"
              :step="1"
              style="width: 100%;"
            />
          </el-form-item>

          <el-form-item label="划线价" prop="original_price">
            <el-input-number
              v-model="formState.original_price"
              :min="0"
              :precision="2"
              :step="1"
              style="width: 100%;"
            />
          </el-form-item>

          <el-form-item label="库存">
            <el-input-number
              v-model="formState.stock"
              :min="0"
              :step="1"
              style="width: 100%;"
            />
          </el-form-item>

          <el-form-item label="销量">
            <el-input-number
              v-model="formState.sales"
              :min="0"
              :step="1"
              style="width: 100%;"
            />
          </el-form-item>

          <el-form-item label="排序值">
            <el-input-number
              v-model="formState.sort_order"
              :min="0"
              :step="1"
              style="width: 100%;"
            />
          </el-form-item>
        </div>

        <el-form-item label="主图" prop="cover_image">
          <div class="media-field">
            <div class="media-toolbar">
              <el-button type="primary" plain :loading="uploadingCover" @click="openCoverPicker">
                上传主图
              </el-button>
              <span class="media-tip">支持 jpg / png / webp，上传成功后自动回填 URL</span>
            </div>

            <el-input
              v-model="formState.cover_image"
              placeholder="可手动填写主图 URL，或点击上方按钮上传"
            />

            <div v-if="formState.cover_image" class="cover-preview">
              <img :src="formState.cover_image" alt="商品主图预览" />
            </div>
          </div>
        </el-form-item>

        <el-form-item label="轮播图">
          <div class="media-field">
            <div class="media-toolbar">
              <el-button plain :loading="uploadingBanner" @click="openBannerPicker">
                上传轮播图
              </el-button>
              <el-button plain @click="addEmptyBannerImage">
                手动新增一项
              </el-button>
              <span class="media-tip">支持多张上传，可上下移动调整展示顺序</span>
            </div>

            <div class="manual-banner-input">
              <el-input
                v-model="manualBannerUrl"
                placeholder="粘贴轮播图 URL 后点击加入列表"
              />
              <el-button @click="addManualBannerImage">加入列表</el-button>
            </div>

            <div v-if="!formState.banner_images.length" class="empty-banner-state">
              暂无轮播图。可直接上传多张图片，或手动新增 URL。
            </div>

            <div v-else class="banner-list">
              <div
                v-for="(image, index) in formState.banner_images"
                :key="`${index}-${image}`"
                class="banner-item"
              >
                <div class="banner-preview" :class="{ 'is-empty': !image }">
                  <img v-if="image" :src="image" :alt="`轮播图 ${index + 1}`" />
                  <span v-else>等待填写或上传</span>
                </div>

                <div class="banner-controls">
                  <el-input
                    v-model="formState.banner_images[index]"
                    placeholder="支持手动填写 URL，或通过上传回填"
                  />

                  <div class="banner-actions">
                    <el-button text :disabled="index === 0" @click="moveBannerImage(index, -1)">
                      上移
                    </el-button>
                    <el-button
                      text
                      :disabled="index === formState.banner_images.length - 1"
                      @click="moveBannerImage(index, 1)"
                    >
                      下移
                    </el-button>
                    <el-button text type="danger" @click="removeBannerImage(index)">
                      删除
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="详情内容">
          <el-input
            v-model="formState.detail_content"
            type="textarea"
            :rows="6"
            placeholder="请输入详情内容字符串"
          />
        </el-form-item>

        <el-form-item label="推荐商品">
          <el-switch
            v-model="formState.is_featured"
            inline-prompt
            active-text="是"
            inactive-text="否"
          />
        </el-form-item>
      </el-form>
    </el-skeleton>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ mode === "create" ? "创建商品" : "保存修改" }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 18px;
}

.media-field {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.media-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.media-tip {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.cover-preview,
.banner-preview {
  width: 168px;
  height: 168px;
  border: 1px dashed var(--el-border-color);
  border-radius: 12px;
  overflow: hidden;
  background: var(--el-fill-color-light);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-preview img,
.banner-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.banner-preview.is-empty {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  text-align: center;
  padding: 12px;
}

.manual-banner-input {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
}

.empty-banner-state {
  padding: 18px;
  border: 1px dashed var(--el-border-color);
  border-radius: 12px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-lighter);
}

.banner-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.banner-item {
  display: grid;
  grid-template-columns: 168px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.banner-controls {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.banner-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.hidden-file-input {
  display: none;
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .manual-banner-input,
  .banner-item {
    grid-template-columns: 1fr;
  }
}
</style>

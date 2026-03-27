<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";

import { createAdminCategory, updateAdminCategory } from "../../api/categories";
import type { AdminCategoryItem, AdminCategoryPayload } from "../../types/admin";

interface CategoryFormState {
  name: string;
  slug: string;
  sort_order: number;
}

const props = defineProps<{
  modelValue: boolean;
  mode: "create" | "edit";
  category: AdminCategoryItem | null;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  submitted: [];
}>();

const formRef = ref<FormInstance>();
const submitting = ref(false);

const formState = reactive<CategoryFormState>({
  name: "",
  slug: "",
  sort_order: 0,
});

const rules: FormRules<CategoryFormState> = {
  name: [
    {
      required: true,
      message: "请输入分类名称",
      trigger: "blur",
    },
  ],
};

function resetForm() {
  formState.name = "";
  formState.slug = "";
  formState.sort_order = 0;
}

function applyCategory(category: AdminCategoryItem | null) {
  if (!category) {
    resetForm();
    return;
  }

  formState.name = category.name;
  formState.slug = category.slug;
  formState.sort_order = category.sort_order;
}

function closeDialog() {
  emit("update:modelValue", false);
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
    const payload: AdminCategoryPayload = {
      name: formState.name.trim(),
      slug: formState.slug.trim() || null,
      sort_order: formState.sort_order,
    };

    if (props.mode === "create") {
      await createAdminCategory(payload);
      ElMessage.success("分类创建成功");
    } else {
      if (!props.category) {
        throw new Error("缺少分类信息，无法编辑");
      }

      await updateAdminCategory(props.category.id, payload);
      ElMessage.success("分类更新成功");
    }

    emit("submitted");
    closeDialog();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "分类提交失败");
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

    applyCategory(props.category);
    formRef.value?.clearValidate();
  },
);

watch(
  () => props.category,
  (category) => {
    if (!props.modelValue) {
      return;
    }

    applyCategory(category);
  },
);
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    :title="mode === 'create' ? '新增分类' : '编辑分类'"
    width="520px"
    destroy-on-close
    :close-on-click-modal="false"
    @close="closeDialog"
  >
    <el-form
      ref="formRef"
      label-position="top"
      :model="formState"
      :rules="rules"
    >
      <el-form-item label="分类名称" prop="name">
        <el-input v-model="formState.name" placeholder="请输入分类名称" />
      </el-form-item>

      <el-form-item label="Slug">
        <el-input
          v-model="formState.slug"
          placeholder="可选；留空则由后端自动生成或保留原值"
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
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ mode === "create" ? "创建分类" : "保存修改" }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
}
</style>

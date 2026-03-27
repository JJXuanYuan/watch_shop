<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

import {
  deleteAdminCategory,
  disableAdminCategory,
  enableAdminCategory,
  fetchAdminCategories,
} from "../../api/categories";
import CategoryFormDialog from "../../components/categories/CategoryFormDialog.vue";
import type { AdminCategoryItem } from "../../types/admin";
import {
  formatDateTime,
  getCategoryStatusLabel,
  getCategoryStatusTagType,
} from "../../utils/format";

const loading = ref(false);
const categories = ref<AdminCategoryItem[]>([]);
const dialogVisible = ref(false);
const dialogMode = ref<"create" | "edit">("create");
const currentCategory = ref<AdminCategoryItem | null>(null);

async function loadCategories() {
  loading.value = true;

  try {
    const response = await fetchAdminCategories();
    categories.value = response.items;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "分类列表加载失败");
  } finally {
    loading.value = false;
  }
}

function openCreateDialog() {
  dialogMode.value = "create";
  currentCategory.value = null;
  dialogVisible.value = true;
}

function openEditDialog(category: AdminCategoryItem) {
  dialogMode.value = "edit";
  currentCategory.value = category;
  dialogVisible.value = true;
}

async function handleToggleStatus(category: AdminCategoryItem) {
  const nextAction = category.status === "enabled" ? "禁用" : "启用";

  try {
    await ElMessageBox.confirm(
      `确认要${nextAction}分类“${category.name}”吗？`,
      `${nextAction}分类`,
      {
        type: "warning",
      },
    );

    if (category.status === "enabled") {
      await disableAdminCategory(category.id);
    } else {
      await enableAdminCategory(category.id);
    }

    ElMessage.success(`分类${nextAction}成功`);
    await loadCategories();
  } catch (error) {
    if (error === "cancel") {
      return;
    }

    ElMessage.error(error instanceof Error ? error.message : `分类${nextAction}失败`);
  }
}

async function handleDelete(category: AdminCategoryItem) {
  try {
    await ElMessageBox.confirm(
      `确认删除分类“${category.name}”吗？`,
      "删除分类",
      {
        type: "warning",
      },
    );

    await deleteAdminCategory(category.id);
    ElMessage.success("分类删除成功");
    await loadCategories();
  } catch (error) {
    if (error === "cancel") {
      return;
    }

    ElMessage.error(error instanceof Error ? error.message : "分类删除失败");
  }
}

function handleSubmitted() {
  void loadCategories();
}

onMounted(() => {
  void loadCategories();
});
</script>

<template>
  <section class="page-shell">
    <el-card class="toolbar-card" shadow="never">
      <div class="page-head">
        <div>
          <p class="page-kicker">Category Admin</p>
          <h3>分类管理</h3>
          <p class="page-summary">支持新增、编辑、启停用和删除，删除失败会直接展示后端保护信息。</p>
        </div>

        <el-button type="primary" @click="openCreateDialog">新增分类</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table :data="categories" v-loading="loading">
        <el-table-column prop="id" label="ID" width="72" />
        <el-table-column prop="name" label="分类名称" min-width="180" />
        <el-table-column prop="slug" label="Slug" min-width="180" />
        <el-table-column prop="sort_order" label="排序值" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getCategoryStatusTagType(row.status)">
              {{ getCategoryStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="product_count" label="商品数" width="100" />
        <el-table-column label="更新时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="260" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
              <el-button link type="warning" @click="handleToggleStatus(row)">
                {{ row.status === "enabled" ? "禁用" : "启用" }}
              </el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <CategoryFormDialog
      v-model="dialogVisible"
      :mode="dialogMode"
      :category="currentCategory"
      @submitted="handleSubmitted"
    />
  </section>
</template>

<style scoped>
.page-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.toolbar-card {
  border-radius: 22px;
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-kicker {
  margin: 0 0 8px;
  color: #9a712d;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.page-head h3 {
  margin: 0;
  font-size: 26px;
}

.page-summary {
  margin: 10px 0 0;
  color: #6c6355;
  font-size: 14px;
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>

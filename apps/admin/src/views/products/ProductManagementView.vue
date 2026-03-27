<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

import { fetchAdminCategories } from "../../api/categories";
import {
  deleteAdminProduct,
  fetchAdminProductDetail,
  fetchAdminProducts,
  putProductOnSale,
  restoreAdminProduct,
  takeProductOffSale,
} from "../../api/products";
import ProductFormDialog from "../../components/products/ProductFormDialog.vue";
import type {
  AdminCategoryItem,
  AdminProductListItem,
  AdminProductResponse,
  ProductDeletedFilter,
  ProductStatus,
} from "../../types/admin";
import {
  formatDateTime,
  formatMoney,
  getProductStatusLabel,
  getProductStatusTagType,
} from "../../utils/format";

interface ProductFilters {
  keyword: string;
  category_id?: number;
  status?: ProductStatus;
  deleted: ProductDeletedFilter;
}

const loading = ref(false);
const detailLoading = ref(false);
const categories = ref<AdminCategoryItem[]>([]);
const products = ref<AdminProductListItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(10);
const dialogVisible = ref(false);
const dialogMode = ref<"create" | "edit">("create");
const currentProduct = ref<AdminProductResponse | null>(null);

const filters = reactive<ProductFilters>({
  keyword: "",
  category_id: undefined,
  status: undefined,
  deleted: "not_deleted",
});

const categoryOptions = computed(() => categories.value);

async function loadCategories() {
  const response = await fetchAdminCategories();
  categories.value = response.items;
}

async function loadProducts() {
  loading.value = true;

  try {
    const response = await fetchAdminProducts({
      page: page.value,
      page_size: pageSize.value,
      keyword: filters.keyword.trim() || undefined,
      category_id: filters.category_id,
      status: filters.status,
      deleted: filters.deleted,
    });

    products.value = response.items;
    total.value = response.total;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "商品列表加载失败");
  } finally {
    loading.value = false;
  }
}

async function initializePage() {
  try {
    await loadCategories();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "分类数据加载失败");
  }

  await loadProducts();
}

function handleSearch() {
  page.value = 1;
  void loadProducts();
}

function handleReset() {
  filters.keyword = "";
  filters.category_id = undefined;
  filters.status = undefined;
  filters.deleted = "not_deleted";
  page.value = 1;
  void loadProducts();
}

function handlePageChange(nextPage: number) {
  page.value = nextPage;
  void loadProducts();
}

function handlePageSizeChange(nextPageSize: number) {
  pageSize.value = nextPageSize;
  page.value = 1;
  void loadProducts();
}

function openCreateDialog() {
  currentProduct.value = null;
  dialogMode.value = "create";
  dialogVisible.value = true;
}

async function openEditDialog(productId: number) {
  dialogMode.value = "edit";
  dialogVisible.value = true;
  detailLoading.value = true;
  currentProduct.value = null;

  try {
    currentProduct.value = await fetchAdminProductDetail(productId);
  } catch (error) {
    dialogVisible.value = false;
    ElMessage.error(error instanceof Error ? error.message : "商品详情加载失败");
  } finally {
    detailLoading.value = false;
  }
}

async function handleToggleSale(row: AdminProductListItem) {
  const nextAction = row.status === "on_sale" ? "下架" : "上架";

  try {
    await ElMessageBox.confirm(
      `确认要${nextAction}商品“${row.name}”吗？`,
      `${nextAction}商品`,
      {
        type: "warning",
      },
    );

    if (row.status === "on_sale") {
      await takeProductOffSale(row.id);
    } else {
      await putProductOnSale(row.id);
    }

    ElMessage.success(`商品${nextAction}成功`);
    await loadProducts();
  } catch (error) {
    if (error === "cancel") {
      return;
    }

    ElMessage.error(error instanceof Error ? error.message : `商品${nextAction}失败`);
  }
}

async function handleDelete(row: AdminProductListItem) {
  try {
    await ElMessageBox.confirm(
      `确认删除商品“${row.name}”吗？删除后会进入回收状态，可在“已删除”筛选中恢复。`,
      "软删除商品",
      {
        type: "warning",
      },
    );

    await deleteAdminProduct(row.id);
    ElMessage.success("商品已移入回收状态");

    if (products.value.length === 1 && page.value > 1) {
      page.value -= 1;
    }

    await loadProducts();
  } catch (error) {
    if (error === "cancel") {
      return;
    }

    ElMessage.error(error instanceof Error ? error.message : "商品删除失败");
  }
}

async function handleRestore(row: AdminProductListItem) {
  try {
    await ElMessageBox.confirm(
      `确认恢复商品“${row.name}”吗？恢复后可继续编辑或重新上架。`,
      "恢复商品",
      {
        type: "warning",
      },
    );

    await restoreAdminProduct(row.id);
    ElMessage.success("商品恢复成功");

    if (products.value.length === 1 && page.value > 1 && filters.deleted === "deleted") {
      page.value -= 1;
    }

    await loadProducts();
  } catch (error) {
    if (error === "cancel") {
      return;
    }

    ElMessage.error(error instanceof Error ? error.message : "商品恢复失败");
  }
}

function handleSubmitted() {
  void Promise.all([loadCategories(), loadProducts()]);
}

onMounted(() => {
  void initializePage();
});
</script>

<template>
  <section class="page-shell">
    <el-card class="toolbar-card" shadow="never">
      <div class="page-head">
        <div>
          <p class="page-kicker">Product Admin</p>
          <h3>商品管理</h3>
          <p class="page-summary">支持软删除、恢复、筛选、创建、编辑和上下架。</p>
        </div>

        <el-button type="primary" @click="openCreateDialog">新增商品</el-button>
      </div>

      <el-form class="filter-form" :inline="true" :model="filters">
        <el-form-item label="商品名">
          <el-input
            v-model="filters.keyword"
            clearable
            placeholder="输入商品名称关键词"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="分类">
          <el-select
            v-model="filters.category_id"
            clearable
            filterable
            placeholder="全部分类"
            style="width: 220px;"
          >
            <el-option
              v-for="category in categoryOptions"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="filters.status"
            clearable
            placeholder="全部状态"
            style="width: 180px;"
          >
            <el-option label="草稿" value="draft" />
            <el-option label="上架中" value="on_sale" />
            <el-option label="已下架" value="off_sale" />
          </el-select>
        </el-form-item>

        <el-form-item label="删除状态">
          <el-select
            v-model="filters.deleted"
            placeholder="删除状态"
            style="width: 180px;"
          >
            <el-option label="未删除" value="not_deleted" />
            <el-option label="已删除" value="deleted" />
            <el-option label="全部" value="all" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="products" v-loading="loading">
        <el-table-column prop="id" label="ID" width="72" />
        <el-table-column label="商品名称" min-width="240">
          <template #default="{ row }">
            <div class="name-cell">
              <span class="name-main">{{ row.name }}</span>
              <span v-if="row.subtitle" class="name-sub">{{ row.subtitle }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="分类" min-width="140">
          <template #default="{ row }">
            {{ row.category.name }} / {{ row.category_id }}
          </template>
        </el-table-column>
        <el-table-column label="售价" min-width="120">
          <template #default="{ row }">¥{{ formatMoney(row.price) }}</template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" width="92" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getProductStatusTagType(row.status)">
              {{ getProductStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="删除状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_deleted ? 'danger' : 'success'">
              {{ row.is_deleted ? "已删除" : "未删除" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序值" width="100" />
        <el-table-column label="更新时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="删除时间" min-width="170">
          <template #default="{ row }">
            {{ row.deleted_at ? formatDateTime(row.deleted_at) : "--" }}
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="280" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <template v-if="row.is_deleted">
                <el-button link type="success" @click="handleRestore(row)">恢复</el-button>
              </template>
              <template v-else>
                <el-button link type="primary" @click="openEditDialog(row.id)">编辑</el-button>
                <el-button link type="warning" @click="handleToggleSale(row)">
                  {{ row.status === "on_sale" ? "下架" : "上架" }}
                </el-button>
                <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
              </template>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next"
          :current-page="page"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
      </div>
    </el-card>

    <ProductFormDialog
      v-model="dialogVisible"
      :mode="dialogMode"
      :categories="categories"
      :product="currentProduct"
      :loading="detailLoading"
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
  margin-bottom: 18px;
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

.filter-form {
  margin-top: 12px;
}

.name-cell {
  display: flex;
  flex-direction: column;
}

.name-main {
  font-weight: 700;
}

.name-sub {
  margin-top: 6px;
  color: #7a6c58;
  font-size: 12px;
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}
</style>

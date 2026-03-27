<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

import { fetchAdminLogisticsCompanies } from "../../api/logisticsCompanies";
import {
  cancelAdminOrder,
  completeAdminOrder,
  fetchAdminOrderDetail,
  fetchAdminOrderLogs,
  fetchAdminOrders,
  prepareAdminOrder,
  shipAdminOrder,
} from "../../api/orders";
import OrderDetailDialog from "../../components/orders/OrderDetailDialog.vue";
import type {
  AdminOrderListItem,
  AdminOrderOperationLog,
  AdminOrderResponse,
  AdminOrderShipPayload,
  FulfillmentStatus,
  LogisticsCompany,
  OrderStatus,
  PaymentStatus,
} from "../../types/admin";
import {
  formatDateTime,
  formatMoney,
  getFulfillmentStatusLabel,
  getFulfillmentStatusTagType,
  getOrderStatusLabel,
  getOrderStatusTagType,
  getPaymentStatusLabel,
  getPaymentStatusTagType,
} from "../../utils/format";

interface OrderFilters {
  order_no: string;
  user_key: string;
  status?: OrderStatus;
  payment_status?: PaymentStatus;
  fulfillment_status?: FulfillmentStatus;
}

interface ShipFormModel {
  shipping_company_code: string;
  shipping_company: string;
  tracking_no: string;
  shipping_note: string;
}

type FulfillmentAction = "prepare" | "complete";

const loading = ref(false);
const detailLoading = ref(false);
const cancelling = ref(false);
const actionLoadingOrderId = ref<number | null>(null);
const actionLoadingType = ref<FulfillmentAction | null>(null);
const orders = ref<AdminOrderListItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(10);
const dialogVisible = ref(false);
const currentOrder = ref<AdminOrderResponse | null>(null);
const currentOrderLogs = ref<AdminOrderOperationLog[]>([]);
const detailLogsLoading = ref(false);
const logisticsCompanies = ref<LogisticsCompany[]>([]);
const logisticsLoading = ref(false);
const shipDialogVisible = ref(false);
const shipDialogLoading = ref(false);
const shipSubmitting = ref(false);
const shipFormRef = ref<FormInstance>();
const shipOrderTarget = ref<AdminOrderResponse | null>(null);

const filters = reactive<OrderFilters>({
  order_no: "",
  user_key: "",
  status: undefined,
  payment_status: undefined,
  fulfillment_status: undefined,
});

const shipForm = reactive<ShipFormModel>({
  shipping_company_code: "",
  shipping_company: "",
  tracking_no: "",
  shipping_note: "",
});

function validateRequiredTrimmed(_: unknown, value: string, callback: (error?: Error) => void) {
  if (!value || !value.trim()) {
    callback(new Error("此项不能为空"));
    return;
  }

  callback();
}

const shipRules: FormRules<ShipFormModel> = {
  shipping_company: [
    {
      validator: validateRequiredTrimmed,
      trigger: "blur",
    },
  ],
  tracking_no: [
    {
      validator: validateRequiredTrimmed,
      trigger: "blur",
    },
  ],
};

function canPrepareOrder(target: Pick<AdminOrderListItem, "status" | "payment_status" | "fulfillment_status">) {
  return (
    target.status === "paid"
    && target.payment_status === "paid"
    && target.fulfillment_status === "unfulfilled"
  );
}

function canShipOrder(target: Pick<AdminOrderListItem, "status" | "payment_status" | "fulfillment_status">) {
  return (
    target.status === "paid"
    && target.payment_status === "paid"
    && target.fulfillment_status === "preparing"
  );
}

function canCompleteOrder(
  target: Pick<AdminOrderListItem, "status" | "payment_status" | "fulfillment_status">,
) {
  return (
    target.status === "paid"
    && target.payment_status === "paid"
    && target.fulfillment_status === "shipped"
  );
}

function getFulfillmentDisplay(target: AdminOrderListItem): string {
  if (target.status !== "paid") {
    return "--";
  }
  return getFulfillmentStatusLabel(target.fulfillment_status);
}

function getShippingCompanyDisplay(
  target: Pick<AdminOrderListItem, "shipping_company" | "shipping_company_code">,
) {
  if (target.shipping_company) {
    return target.shipping_company;
  }

  if (target.shipping_company_code) {
    return `物流公司 ${target.shipping_company_code}`;
  }

  return "--";
}

function getShippingSummary(
  target: Pick<
    AdminOrderListItem,
    "shipping_company" | "shipping_company_code" | "tracking_no" | "shipped_at"
  >,
) {
  const company = getShippingCompanyDisplay(target);
  const parts = [company !== "--" ? company : null, target.tracking_no].filter(Boolean);
  if (!parts.length) {
    return "--";
  }

  const summary = parts.join(" / ");
  if (!target.shipped_at) {
    return summary;
  }

  return `${summary} · ${formatDateTime(target.shipped_at)}`;
}

function isActionLoading(orderId: number, action: FulfillmentAction) {
  return actionLoadingOrderId.value === orderId && actionLoadingType.value === action;
}

function resetShipForm() {
  shipForm.shipping_company_code = "";
  shipForm.shipping_company = "";
  shipForm.tracking_no = "";
  shipForm.shipping_note = "";
  shipOrderTarget.value = null;
  shipFormRef.value?.clearValidate();
}

async function loadLogisticsCompanies(silent = true) {
  if (logisticsLoading.value) {
    return;
  }

  logisticsLoading.value = true;

  try {
    const response = await fetchAdminLogisticsCompanies();
    logisticsCompanies.value = response.items;
  } catch (error) {
    if (!silent) {
      ElMessage.error(error instanceof Error ? error.message : "物流公司字典加载失败");
    }
  } finally {
    logisticsLoading.value = false;
  }
}

function handleShippingCompanyCodeChange(value?: string) {
  shipForm.shipping_company_code = value ?? "";

  if (!value) {
    shipForm.shipping_company = "";
    return;
  }

  const company = logisticsCompanies.value.find((item) => item.code === value);
  shipForm.shipping_company = company?.name ?? "";
}

async function loadOrders() {
  loading.value = true;

  try {
    const response = await fetchAdminOrders({
      page: page.value,
      page_size: pageSize.value,
      order_no: filters.order_no.trim() || undefined,
      user_key: filters.user_key.trim() || undefined,
      status: filters.status,
      payment_status: filters.payment_status,
      fulfillment_status: filters.fulfillment_status,
    });

    orders.value = response.items;
    total.value = response.total;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "订单列表加载失败");
  } finally {
    loading.value = false;
  }
}

function handleSearch() {
  page.value = 1;
  void loadOrders();
}

function handleReset() {
  filters.order_no = "";
  filters.user_key = "";
  filters.status = undefined;
  filters.payment_status = undefined;
  filters.fulfillment_status = undefined;
  page.value = 1;
  void loadOrders();
}

function handlePageChange(nextPage: number) {
  page.value = nextPage;
  void loadOrders();
}

function handlePageSizeChange(nextPageSize: number) {
  pageSize.value = nextPageSize;
  page.value = 1;
  void loadOrders();
}

async function openDetailDialog(orderId: number) {
  dialogVisible.value = true;
  detailLoading.value = true;
  detailLogsLoading.value = true;
  currentOrder.value = null;
  currentOrderLogs.value = [];

  try {
    const [detailResult, logsResult] = await Promise.allSettled([
      fetchAdminOrderDetail(orderId),
      fetchAdminOrderLogs(orderId),
    ]);

    if (detailResult.status === "rejected") {
      throw detailResult.reason;
    }

    currentOrder.value = detailResult.value;

    if (logsResult.status === "fulfilled") {
      currentOrderLogs.value = logsResult.value.items;
    } else {
      currentOrderLogs.value = [];
      ElMessage.error(logsResult.reason instanceof Error ? logsResult.reason.message : "订单日志加载失败");
    }
  } catch (error) {
    dialogVisible.value = false;
    ElMessage.error(error instanceof Error ? error.message : "订单详情加载失败");
  } finally {
    detailLoading.value = false;
    detailLogsLoading.value = false;
  }
}

async function refreshCurrentOrder() {
  if (!currentOrder.value) {
    return;
  }

  currentOrder.value = await fetchAdminOrderDetail(currentOrder.value.id);
}

async function refreshCurrentOrderLogs() {
  if (!currentOrder.value) {
    currentOrderLogs.value = [];
    return;
  }

  const response = await fetchAdminOrderLogs(currentOrder.value.id);
  currentOrderLogs.value = response.items;
}

async function refreshViews(orderId?: number) {
  const tasks: Promise<unknown>[] = [loadOrders()];

  if (dialogVisible.value && currentOrder.value && (!orderId || currentOrder.value.id === orderId)) {
    tasks.push(refreshCurrentOrder());
    tasks.push(refreshCurrentOrderLogs());
  }

  await Promise.all(tasks);
}

async function runCancel(orderId: number) {
  await cancelAdminOrder(orderId);
  await refreshViews(orderId);
}

async function handleCancelOrder(target: AdminOrderListItem | AdminOrderResponse) {
  if (!target.can_cancel) {
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确认取消订单“${target.order_no}”吗？取消后会回补库存。`,
      "取消订单",
      {
        type: "warning",
      },
    );

    cancelling.value = true;
    await runCancel(target.id);
    ElMessage.success("订单取消成功");
  } catch (error) {
    if (error === "cancel") {
      return;
    }

    ElMessage.error(error instanceof Error ? error.message : "订单取消失败");
  } finally {
    cancelling.value = false;
  }
}

function handleCurrentOrderCancel() {
  if (!currentOrder.value) {
    return;
  }

  void handleCancelOrder(currentOrder.value);
}

function handleCurrentOrderPrepare() {
  if (!currentOrder.value) {
    return;
  }

  void handlePrepareOrder(currentOrder.value);
}

function handleCurrentOrderComplete() {
  if (!currentOrder.value) {
    return;
  }

  void handleCompleteOrder(currentOrder.value);
}

async function handlePrepareOrder(target: AdminOrderListItem | AdminOrderResponse) {
  if (!canPrepareOrder(target)) {
    return;
  }

  actionLoadingOrderId.value = target.id;
  actionLoadingType.value = "prepare";

  try {
    await prepareAdminOrder(target.id);
    await refreshViews(target.id);
    ElMessage.success("订单已进入备货中");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "备货操作失败");
  } finally {
    actionLoadingOrderId.value = null;
    actionLoadingType.value = null;
  }
}

async function handleCompleteOrder(target: AdminOrderListItem | AdminOrderResponse) {
  if (!canCompleteOrder(target)) {
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确认将订单“${target.order_no}”标记为已完成吗？`,
      "完成履约",
      {
        type: "warning",
      },
    );

    actionLoadingOrderId.value = target.id;
    actionLoadingType.value = "complete";

    await completeAdminOrder(target.id);
    await refreshViews(target.id);
    ElMessage.success("订单已完成");
  } catch (error) {
    if (error === "cancel") {
      return;
    }

    ElMessage.error(error instanceof Error ? error.message : "完成操作失败");
  } finally {
    actionLoadingOrderId.value = null;
    actionLoadingType.value = null;
  }
}

async function openShipDialog(orderId: number) {
  shipDialogLoading.value = true;

  try {
    if (!logisticsCompanies.value.length) {
      await loadLogisticsCompanies(false);
    }

    const detail
      = currentOrder.value?.id === orderId ? currentOrder.value : await fetchAdminOrderDetail(orderId);

    if (!canShipOrder(detail)) {
      throw new Error("当前订单状态不支持发货");
    }

    shipOrderTarget.value = detail;
    shipForm.shipping_company_code = detail.shipping_company_code ?? "";
    shipForm.shipping_company = detail.shipping_company ?? "";
    shipForm.tracking_no = detail.tracking_no ?? "";
    shipForm.shipping_note = detail.shipping_note ?? "";
    shipDialogVisible.value = true;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "发货信息加载失败");
  } finally {
    shipDialogLoading.value = false;
  }
}

function handleCurrentOrderShip() {
  if (!currentOrder.value) {
    return;
  }

  void openShipDialog(currentOrder.value.id);
}

async function submitShipOrder() {
  if (!shipOrderTarget.value || !shipFormRef.value) {
    return;
  }

  try {
    await shipFormRef.value.validate();
  } catch {
    return;
  }

  shipSubmitting.value = true;

  try {
    const payload: AdminOrderShipPayload = {
      shipping_company_code: shipForm.shipping_company_code.trim() || null,
      shipping_company: shipForm.shipping_company.trim() || null,
      tracking_no: shipForm.tracking_no.trim(),
      shipping_note: shipForm.shipping_note.trim() || null,
    };

    const targetOrderId = shipOrderTarget.value.id;
    await shipAdminOrder(targetOrderId, payload);
    shipDialogVisible.value = false;
    resetShipForm();
    await refreshViews(targetOrderId);
    ElMessage.success("订单发货成功");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "发货失败");
  } finally {
    shipSubmitting.value = false;
  }
}

function handleShipDialogClosed() {
  resetShipForm();
}

onMounted(() => {
  void loadOrders();
  void loadLogisticsCompanies();
});
</script>

<template>
  <section class="page-shell">
    <el-card class="toolbar-card" shadow="never">
      <div class="page-head">
        <div>
          <p class="page-kicker">Order Admin</p>
          <h3>订单管理</h3>
          <p class="page-summary">支持按订单号、用户标识、订单状态、支付状态、履约状态筛选，并执行备货、发货、完成等最小履约操作。</p>
        </div>
      </div>

      <el-form class="filter-form" :inline="true" :model="filters">
        <el-form-item label="订单号">
          <el-input
            v-model="filters.order_no"
            clearable
            placeholder="输入订单号关键词"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="用户标识">
          <el-input
            v-model="filters.user_key"
            clearable
            placeholder="输入 user_key"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="filters.status"
            clearable
            placeholder="全部状态"
            style="width: 180px;"
          >
            <el-option label="待支付" value="pending" />
            <el-option label="已支付" value="paid" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>

        <el-form-item label="支付状态">
          <el-select
            v-model="filters.payment_status"
            clearable
            placeholder="全部支付状态"
            style="width: 180px;"
          >
            <el-option label="未支付" value="unpaid" />
            <el-option label="已支付" value="paid" />
          </el-select>
        </el-form-item>

        <el-form-item label="履约状态">
          <el-select
            v-model="filters.fulfillment_status"
            clearable
            placeholder="全部履约状态"
            style="width: 180px;"
          >
            <el-option label="待发货" value="unfulfilled" />
            <el-option label="备货中" value="preparing" />
            <el-option label="已发货" value="shipped" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="orders" v-loading="loading">
        <el-table-column prop="id" label="ID" width="72" />
        <el-table-column prop="order_no" label="订单号" min-width="220" />
        <el-table-column prop="user_key" label="用户标识" min-width="180" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getOrderStatusTagType(row.status)">
              {{ getOrderStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="支付状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getPaymentStatusTagType(row.payment_status)">
              {{ getPaymentStatusLabel(row.payment_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="履约状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === 'paid' ? getFulfillmentStatusTagType(row.fulfillment_status) : 'info'">
              {{ getFulfillmentDisplay(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="130">
          <template #default="{ row }">¥{{ formatMoney(row.total_amount) }}</template>
        </el-table-column>
        <el-table-column label="收货人" min-width="150">
          <template #default="{ row }">
            {{ row.receiver_name || "--" }}{{ row.receiver_phone ? ` / ${row.receiver_phone}` : "" }}
          </template>
        </el-table-column>
        <el-table-column label="发货信息" min-width="240">
          <template #default="{ row }">
            {{ getShippingSummary(row) }}
          </template>
        </el-table-column>
        <el-table-column label="订单项数" width="100">
          <template #default="{ row }">{{ row.item_count }}</template>
        </el-table-column>
        <el-table-column label="商品总数" width="100">
          <template #default="{ row }">{{ row.total_quantity }}</template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="支付时间" min-width="170">
          <template #default="{ row }">{{ row.paid_at ? formatDateTime(row.paid_at) : "--" }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="280" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button link type="primary" @click="openDetailDialog(row.id)">详情</el-button>
              <el-button
                v-if="canPrepareOrder(row)"
                link
                type="warning"
                :loading="isActionLoading(row.id, 'prepare')"
                @click="handlePrepareOrder(row)"
              >
                备货
              </el-button>
              <el-button
                v-if="canShipOrder(row)"
                link
                type="primary"
                :loading="shipSubmitting && shipOrderTarget?.id === row.id"
                @click="openShipDialog(row.id)"
              >
                发货
              </el-button>
              <el-button
                v-if="canCompleteOrder(row)"
                link
                type="success"
                :loading="isActionLoading(row.id, 'complete')"
                @click="handleCompleteOrder(row)"
              >
                完成
              </el-button>
              <el-button
                v-if="row.can_cancel"
                link
                type="danger"
                :loading="cancelling"
                @click="handleCancelOrder(row)"
              >
                取消订单
              </el-button>
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

    <OrderDetailDialog
      v-model="dialogVisible"
      :order="currentOrder"
      :logs="currentOrderLogs"
      :loading="detailLoading"
      :logs-loading="detailLogsLoading"
      :cancelling="cancelling"
      :prepare-loading="Boolean(currentOrder && isActionLoading(currentOrder.id, 'prepare'))"
      :ship-loading="shipDialogLoading || (shipSubmitting && shipOrderTarget?.id === currentOrder?.id)"
      :complete-loading="Boolean(currentOrder && isActionLoading(currentOrder.id, 'complete'))"
      @cancel-order="handleCurrentOrderCancel"
      @prepare-order="handleCurrentOrderPrepare"
      @ship-order="handleCurrentOrderShip"
      @complete-order="handleCurrentOrderComplete"
    />

    <el-dialog
      v-model="shipDialogVisible"
      title="录入发货信息"
      width="520px"
      destroy-on-close
      @closed="handleShipDialogClosed"
    >
      <el-skeleton :loading="shipDialogLoading" animated>
        <template #template>
          <el-skeleton-item variant="text" style="width: 100%; height: 28px;" />
          <el-skeleton-item variant="text" style="width: 100%; height: 180px; margin-top: 18px;" />
        </template>

        <template v-if="shipOrderTarget">
          <div class="ship-dialog-meta">
            <p>订单号：{{ shipOrderTarget.order_no }}</p>
            <p>履约状态：{{ getFulfillmentStatusLabel(shipOrderTarget.fulfillment_status) }}</p>
          </div>

          <el-form ref="shipFormRef" :model="shipForm" :rules="shipRules" label-width="88px">
            <el-form-item label="快递公司" prop="shipping_company">
              <div class="shipping-company-field">
                <el-select
                  v-model="shipForm.shipping_company_code"
                  clearable
                  filterable
                  placeholder="优先选择常用物流公司"
                  :loading="logisticsLoading"
                  @change="handleShippingCompanyCodeChange"
                  @clear="handleShippingCompanyCodeChange(undefined)"
                >
                  <el-option
                    v-for="company in logisticsCompanies"
                    :key="company.id"
                    :label="company.name"
                    :value="company.code"
                  />
                </el-select>
                <el-input
                  v-model="shipForm.shipping_company"
                  :disabled="Boolean(shipForm.shipping_company_code)"
                  maxlength="100"
                  :placeholder="shipForm.shipping_company_code ? '已根据所选物流公司自动带出' : '如无匹配公司，可手动输入公司名称'"
                />
                <p class="field-hint">优先从物流公司字典选择；若没有匹配项，可清空选择后手动输入。</p>
              </div>
            </el-form-item>
            <el-form-item label="快递单号" prop="tracking_no">
              <el-input
                v-model="shipForm.tracking_no"
                maxlength="64"
                placeholder="请输入快递单号"
              />
            </el-form-item>
            <el-form-item label="备注">
              <el-input
                v-model="shipForm.shipping_note"
                type="textarea"
                :rows="3"
                maxlength="255"
                show-word-limit
                placeholder="可选，记录打包或发货备注"
              />
            </el-form-item>
          </el-form>
        </template>
      </el-skeleton>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="shipDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="shipSubmitting" @click="submitShipOrder">
            确认发货
          </el-button>
        </div>
      </template>
    </el-dialog>
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

.table-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.ship-dialog-meta {
  margin-bottom: 16px;
  color: #6c6355;
  font-size: 14px;
  line-height: 1.7;
}

.ship-dialog-meta p {
  margin: 0;
}

.ship-dialog-meta p + p {
  margin-top: 6px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.shipping-company-field {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.field-hint {
  margin: 0;
  color: #6c6355;
  font-size: 12px;
  line-height: 1.6;
}
</style>

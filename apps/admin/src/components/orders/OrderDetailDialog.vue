<script setup lang="ts">
import { computed } from "vue";
import { ElMessage } from "element-plus";

import type { AdminOrderOperationLog, AdminOrderResponse } from "../../types/admin";
import {
  formatDateTime,
  formatMoney,
  getFulfillmentStatusLabel,
  getOrderStatusLabel,
  getFulfillmentStatusTagType,
  getOrderStatusTagType,
  getPaymentStatusLabel,
  getPaymentStatusTagType,
} from "../../utils/format";

const props = defineProps<{
  modelValue: boolean;
  order: AdminOrderResponse | null;
  logs?: AdminOrderOperationLog[];
  loading?: boolean;
  logsLoading?: boolean;
  cancelling?: boolean;
  prepareLoading?: boolean;
  shipLoading?: boolean;
  completeLoading?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  cancelOrder: [];
  prepareOrder: [];
  shipOrder: [];
  completeOrder: [];
}>();

const visibleLogs = computed(() => props.logs ?? []);

function closeDialog() {
  emit("update:modelValue", false);
}

function handleCancelOrder() {
  emit("cancelOrder");
}

function getFulfillmentDisplay() {
  if (!props.order || props.order.status !== "paid") {
    return "--";
  }
  return getFulfillmentStatusLabel(props.order.fulfillment_status);
}

function getShippingCompanyDisplay() {
  if (props.order?.shipping_company) {
    return props.order.shipping_company;
  }

  if (props.order?.shipping_company_code) {
    return `物流公司 ${props.order.shipping_company_code}`;
  }

  return "--";
}

function canPrepareOrder() {
  return (
    props.order?.status === "paid"
    && props.order.payment_status === "paid"
    && props.order.fulfillment_status === "unfulfilled"
  );
}

function canShipOrder() {
  return (
    props.order?.status === "paid"
    && props.order.payment_status === "paid"
    && props.order.fulfillment_status === "preparing"
  );
}

function canCompleteOrder() {
  return (
    props.order?.status === "paid"
    && props.order.payment_status === "paid"
    && props.order.fulfillment_status === "shipped"
  );
}

function handlePrepareOrder() {
  emit("prepareOrder");
}

function handleShipOrder() {
  emit("shipOrder");
}

function handleCompleteOrder() {
  emit("completeOrder");
}

function resolveStringDetail(
  log: AdminOrderOperationLog,
  key: "shipping_company_code" | "shipping_company" | "tracking_no" | "shipping_note" | "shipped_at" | "completed_at",
) {
  const value = log.detail?.[key];
  return typeof value === "string" && value ? value : null;
}

function resolveBooleanDetail(
  log: AdminOrderOperationLog,
  key: "inventory_restocked",
) {
  const value = log.detail?.[key];
  return typeof value === "boolean" ? value : null;
}

function getStatusChangeLines(log: AdminOrderOperationLog): string[] {
  const lines: string[] = [];

  if (
    log.before_status
    && log.after_status
    && log.before_status !== log.after_status
  ) {
    lines.push(`订单状态：${getOrderStatusLabel(log.before_status)} -> ${getOrderStatusLabel(log.after_status)}`);
  }

  if (
    log.before_fulfillment_status
    && log.after_fulfillment_status
    && log.before_fulfillment_status !== log.after_fulfillment_status
  ) {
    lines.push(
      `履约状态：${getFulfillmentStatusLabel(log.before_fulfillment_status)} -> ${getFulfillmentStatusLabel(log.after_fulfillment_status)}`,
    );
  }

  if (!lines.length) {
    lines.push("状态未发生变化");
  }

  return lines;
}

function getDetailLines(log: AdminOrderOperationLog): string[] {
  const lines: string[] = [];
  const shippingCompanyCode = resolveStringDetail(log, "shipping_company_code");
  const shippingCompany = resolveStringDetail(log, "shipping_company");
  const trackingNo = resolveStringDetail(log, "tracking_no");
  const shippingNote = resolveStringDetail(log, "shipping_note");
  const shippedAt = resolveStringDetail(log, "shipped_at");
  const completedAt = resolveStringDetail(log, "completed_at");
  const inventoryRestocked = resolveBooleanDetail(log, "inventory_restocked");

  if (shippingCompanyCode) {
    lines.push(`物流编码：${shippingCompanyCode}`);
  }
  if (shippingCompany) {
    lines.push(`快递公司：${shippingCompany}`);
  }
  if (trackingNo) {
    lines.push(`快递单号：${trackingNo}`);
  }
  if (shippingNote) {
    lines.push(`备注：${shippingNote}`);
  }
  if (shippedAt) {
    lines.push(`发货时间：${formatDateTime(shippedAt)}`);
  }
  if (completedAt) {
    lines.push(`完成时间：${formatDateTime(completedAt)}`);
  }
  if (inventoryRestocked) {
    lines.push("库存已回补");
  }

  return lines;
}

async function handleCopyTrackingNo() {
  if (!props.order?.tracking_no) {
    return;
  }

  try {
    await navigator.clipboard.writeText(props.order.tracking_no);
    ElMessage.success("快递单号已复制");
  } catch {
    ElMessage.error("复制失败，请手动复制");
  }
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="订单详情"
    width="980px"
    destroy-on-close
    :close-on-click-modal="false"
    @close="closeDialog"
  >
    <el-skeleton :loading="Boolean(loading)" animated>
      <template #template>
        <el-skeleton-item variant="text" style="width: 100%; height: 28px;" />
        <el-skeleton-item variant="text" style="width: 100%; height: 280px; margin-top: 18px;" />
      </template>

      <template v-if="order">
        <el-descriptions :column="2" border class="detail-descriptions">
          <el-descriptions-item label="订单号">{{ order.order_no }}</el-descriptions-item>
          <el-descriptions-item label="用户标识">{{ order.user_key }}</el-descriptions-item>
          <el-descriptions-item label="订单状态">
            <el-tag :type="getOrderStatusTagType(order.status)">
              {{ getOrderStatusLabel(order.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="支付状态">
            <el-tag :type="getPaymentStatusTagType(order.payment_status)">
              {{ getPaymentStatusLabel(order.payment_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="履约状态">
            <el-tag :type="order.status === 'paid' ? getFulfillmentStatusTagType(order.fulfillment_status) : 'info'">
              {{ getFulfillmentDisplay() }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="下单时间">
            {{ formatDateTime(order.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="支付时间">
            {{ order.paid_at ? formatDateTime(order.paid_at) : "--" }}
          </el-descriptions-item>
          <el-descriptions-item label="订单金额">
            ¥{{ formatMoney(order.total_amount) }}
          </el-descriptions-item>
          <el-descriptions-item label="交易号">
            {{ order.transaction_id || "--" }}
          </el-descriptions-item>
          <el-descriptions-item label="商品数量">
            {{ order.total_quantity }} 件 / {{ order.item_count }} 行
          </el-descriptions-item>
        </el-descriptions>

        <el-descriptions :column="1" border class="detail-descriptions">
          <el-descriptions-item label="收货信息">
            <template v-if="order.address">
              {{ order.address.receiver_name }} / {{ order.address.receiver_phone }} / {{ order.address.full_address }}
            </template>
            <template v-else>--</template>
          </el-descriptions-item>
        </el-descriptions>

        <el-descriptions :column="2" border class="detail-descriptions">
          <el-descriptions-item label="快递公司">
            {{ getShippingCompanyDisplay() }}
          </el-descriptions-item>
          <el-descriptions-item label="快递单号">
            <div class="tracking-row">
              <span>{{ order.tracking_no || "--" }}</span>
              <el-button
                v-if="order.tracking_no"
                link
                type="primary"
                @click="handleCopyTrackingNo"
              >
                复制单号
              </el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="发货时间">
            {{ order.shipped_at ? formatDateTime(order.shipped_at) : "--" }}
          </el-descriptions-item>
          <el-descriptions-item label="完成时间">
            {{ order.completed_at ? formatDateTime(order.completed_at) : "--" }}
          </el-descriptions-item>
          <el-descriptions-item label="发货备注" :span="2">
            {{ order.shipping_note || "--" }}
          </el-descriptions-item>
        </el-descriptions>

        <el-table :data="order.items" class="items-table">
          <el-table-column prop="id" label="订单项 ID" width="100" />
          <el-table-column prop="product_id" label="商品 ID" width="100" />
          <el-table-column prop="product_name_snapshot" label="商品快照名称" min-width="260" />
          <el-table-column label="单价" width="140">
            <template #default="{ row }">¥{{ formatMoney(row.price_snapshot) }}</template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="90" />
          <el-table-column label="小计" width="140">
            <template #default="{ row }">¥{{ formatMoney(row.subtotal_amount) }}</template>
          </el-table-column>
        </el-table>

        <div class="logs-section">
          <div class="logs-head">
            <h4>操作日志</h4>
            <p>记录后台管理员对订单执行的关键动作与履约推进过程。</p>
          </div>

          <el-skeleton :loading="Boolean(logsLoading)" animated>
            <template #template>
              <el-skeleton-item variant="text" style="width: 100%; height: 24px;" />
              <el-skeleton-item variant="text" style="width: 100%; height: 92px; margin-top: 14px;" />
              <el-skeleton-item variant="text" style="width: 100%; height: 92px; margin-top: 14px;" />
            </template>

            <template v-if="visibleLogs.length">
              <el-timeline>
                <el-timeline-item
                  v-for="log in visibleLogs"
                  :key="log.log_id"
                  :timestamp="formatDateTime(log.created_at)"
                  placement="top"
                >
                  <div class="log-entry">
                    <div class="log-entry-head">
                      <strong>{{ log.action_label }}</strong>
                      <span>{{ log.operator_username || "系统" }}</span>
                    </div>
                    <p
                      v-for="line in getStatusChangeLines(log)"
                      :key="`${log.log_id}-status-${line}`"
                      class="log-line"
                    >
                      {{ line }}
                    </p>
                    <p
                      v-for="line in getDetailLines(log)"
                      :key="`${log.log_id}-detail-${line}`"
                      class="log-line log-line--muted"
                    >
                      {{ line }}
                    </p>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </template>

            <el-empty v-else description="暂无操作日志" />
          </el-skeleton>
        </div>
      </template>
    </el-skeleton>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="closeDialog">关闭</el-button>
        <el-button
          v-if="canPrepareOrder()"
          type="warning"
          :loading="prepareLoading"
          @click="handlePrepareOrder"
        >
          备货
        </el-button>
        <el-button
          v-if="canShipOrder()"
          type="primary"
          :loading="shipLoading"
          @click="handleShipOrder"
        >
          发货
        </el-button>
        <el-button
          v-if="canCompleteOrder()"
          type="success"
          :loading="completeLoading"
          @click="handleCompleteOrder"
        >
          完成
        </el-button>
        <el-button
          v-if="order?.can_cancel"
          type="danger"
          :loading="cancelling"
          @click="handleCancelOrder"
        >
          取消订单
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.detail-descriptions {
  margin-bottom: 18px;
}

.items-table {
  margin-top: 18px;
}

.logs-section {
  margin-top: 24px;
  padding: 20px 18px 8px;
  border: 1px solid rgba(154, 113, 45, 0.12);
  border-radius: 16px;
  background: #fcfaf6;
}

.logs-head {
  margin-bottom: 16px;
}

.logs-head h4 {
  margin: 0;
  font-size: 16px;
}

.logs-head p {
  margin: 8px 0 0;
  color: #6c6355;
  font-size: 13px;
}

.log-entry {
  padding: 4px 0 10px;
}

.log-entry-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 8px;
  color: #2f2619;
}

.log-entry-head span {
  color: #6c6355;
  font-size: 13px;
}

.log-line {
  margin: 6px 0 0;
  color: #2f2619;
  font-size: 13px;
  line-height: 1.7;
}

.log-line--muted {
  color: #6c6355;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.tracking-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>

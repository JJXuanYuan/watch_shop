<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { adminUsername, clearAdminSession } from "../auth/session";

const route = useRoute();
const router = useRouter();

const pageTitle = computed(() => String(route.meta.title ?? "后台管理"));

function handleLogout() {
  clearAdminSession();
  void router.push({
    name: "login",
  });
}
</script>

<template>
  <el-container class="admin-shell">
    <el-aside class="admin-aside" width="240px">
      <div class="brand">
        <p class="brand-kicker">Watch Shop</p>
        <h1>管理后台</h1>
        <p class="brand-subtitle">商品、分类与管理员操作入口</p>
      </div>

        <el-menu
          class="nav-menu"
          :default-active="route.path"
          router
        >
          <el-menu-item index="/products">商品管理</el-menu-item>
          <el-menu-item index="/categories">分类管理</el-menu-item>
          <el-menu-item index="/orders">订单管理</el-menu-item>
        </el-menu>
      </el-aside>

    <el-container>
      <el-header class="admin-header">
        <div>
          <p class="header-kicker">Admin Console</p>
          <h2>{{ pageTitle }}</h2>
        </div>

        <div class="header-actions">
          <el-tag type="warning" effect="dark">{{ adminUsername || "管理员" }}</el-tag>
          <el-button link type="primary" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>

      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.admin-shell {
  min-height: 100vh;
}

.admin-aside {
  padding: 28px 18px 24px;
  background:
    linear-gradient(180deg, rgba(28, 24, 18, 0.96), rgba(45, 37, 27, 0.98)),
    #1e1710;
  color: #f5e9d5;
}

.brand {
  padding: 10px 14px 24px;
}

.brand-kicker {
  margin: 0 0 10px;
  color: #f2c879;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}

.brand h1 {
  margin: 0;
  font-size: 30px;
}

.brand-subtitle {
  margin: 12px 0 0;
  color: rgba(245, 233, 213, 0.72);
  font-size: 14px;
  line-height: 1.7;
}

.nav-menu {
  border-right: none;
  background: transparent;
}

.nav-menu :deep(.el-menu-item) {
  margin-bottom: 10px;
  border-radius: 16px;
  color: rgba(245, 233, 213, 0.88);
}

.nav-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(246, 205, 121, 0.22), rgba(255, 248, 230, 0.08));
  color: #fff4dc;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88px;
  padding: 18px 28px;
  background: rgba(255, 252, 247, 0.86);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid rgba(95, 73, 30, 0.08);
}

.header-kicker {
  margin: 0 0 6px;
  color: #8f6a2d;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.admin-header h2 {
  margin: 0;
  font-size: 28px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.admin-main {
  padding: 28px;
}
</style>

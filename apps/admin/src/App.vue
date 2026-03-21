<script setup lang="ts">
const panels = [
  {
    title: "工程状态",
    description: "管理后台占位首页已接通，后续可继续扩展登录、商品、订单与运营模块。",
  },
  {
    title: "接口约定",
    description: "默认通过 VITE_API_BASE_URL 访问后端，当前建议开发环境直连 http://localhost:8000。",
  },
  {
    title: "部署方向",
    description: "生产环境由 Nginx 承载静态资源，并将 /api 与 /health 反向代理到 FastAPI。",
  },
];

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
</script>

<template>
  <div class="shell">
    <section class="hero">
      <p class="eyebrow">Watch Shop Admin</p>
      <h1>商城后台基础工程已就绪</h1>
      <p class="summary">
        当前阶段只保留工程、部署和基础联调入口，不包含业务页面与权限体系。
      </p>
    </section>

    <section class="grid">
      <el-card v-for="panel in panels" :key="panel.title" class="panel" shadow="hover">
        <template #header>
          <span>{{ panel.title }}</span>
        </template>
        <p>{{ panel.description }}</p>
      </el-card>
    </section>

    <el-alert
      class="notice"
      type="success"
      :closable="false"
      title="后端健康检查接口已预留为 GET /health"
      description="当前前端 API Base URL 会从环境变量读取，未配置时回落为 /api。"
      show-icon
    />

    <div class="meta">
      <span>API Base URL</span>
      <code>{{ apiBaseUrl }}</code>
    </div>
  </div>
</template>

<style scoped>
:global(body) {
  margin: 0;
  min-width: 320px;
  background:
    radial-gradient(circle at top left, rgba(184, 134, 11, 0.22), transparent 34%),
    linear-gradient(135deg, #f7f2e9 0%, #ece3d3 100%);
  color: #1d1d1f;
  font-family: "IBM Plex Sans", "Noto Sans SC", "Segoe UI", sans-serif;
}

:global(*) {
  box-sizing: border-box;
}

.shell {
  min-height: 100vh;
  padding: 48px 20px 40px;
}

.hero {
  max-width: 960px;
  margin: 0 auto 24px;
  padding: 32px;
  border: 1px solid rgba(109, 80, 34, 0.14);
  border-radius: 28px;
  background: rgba(255, 253, 249, 0.82);
  backdrop-filter: blur(12px);
  box-shadow: 0 24px 48px rgba(86, 63, 26, 0.12);
}

.eyebrow {
  margin: 0 0 12px;
  color: #8c6a2a;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.24em;
  text-transform: uppercase;
}

h1 {
  margin: 0 0 16px;
  font-size: clamp(32px, 5vw, 52px);
  line-height: 1.1;
}

.summary {
  margin: 0;
  max-width: 640px;
  color: #5f5443;
  font-size: 16px;
  line-height: 1.7;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  max-width: 960px;
  margin: 0 auto 20px;
}

.panel {
  border-radius: 22px;
  border: none;
  background: rgba(255, 255, 255, 0.84);
}

.panel p {
  margin: 0;
  color: #4f4638;
  line-height: 1.7;
}

.notice {
  max-width: 960px;
  margin: 0 auto 20px;
}

.meta {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  max-width: 960px;
  margin: 0 auto;
  padding: 18px 20px;
  border-radius: 20px;
  background: rgba(33, 24, 11, 0.92);
  color: #f6ead7;
}

.meta code {
  color: #f9d48c;
  font-size: 14px;
}

@media (max-width: 640px) {
  .shell {
    padding-top: 24px;
  }

  .hero {
    padding: 24px;
    border-radius: 22px;
  }

  .meta {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>


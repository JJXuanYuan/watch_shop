<script setup lang="ts">
import { reactive, ref } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { loginAdmin } from "../api/auth";
import { setAdminSession } from "../auth/session";

interface LoginFormState {
  username: string;
  password: string;
}

const route = useRoute();
const router = useRouter();
const formRef = ref<FormInstance>();
const submitting = ref(false);

const formState = reactive<LoginFormState>({
  username: "",
  password: "",
});

const rules: FormRules<LoginFormState> = {
  username: [
    {
      required: true,
      message: "请输入管理员账号",
      trigger: "blur",
    },
  ],
  password: [
    {
      required: true,
      message: "请输入密码",
      trigger: "blur",
    },
  ],
};

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
    const response = await loginAdmin({
      username: formState.username.trim(),
      password: formState.password,
    });

    setAdminSession(response.access_token, response.username);
    ElMessage.success("登录成功");

    const redirectTarget =
      typeof route.query.redirect === "string" ? route.query.redirect : "/products";
    void router.push(redirectTarget);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "登录失败");
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <section class="login-card">
      <div class="login-copy">
        <p class="eyebrow">Watch Shop Admin</p>
        <h1>管理员登录</h1>
        <p class="summary">
          当前阶段登录基于数据库管理员账号校验。
          本地开发默认管理员会通过 seed 脚本初始化，生产环境必须尽快修改默认密码。
        </p>
      </div>

      <el-form
        ref="formRef"
        class="login-form"
        :model="formState"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formState.username"
            size="large"
            placeholder="请输入管理员用户名"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="formState.password"
            size="large"
            type="password"
            show-password
            placeholder="请输入管理员密码"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>

        <el-button
          class="login-button"
          type="primary"
          size="large"
          :loading="submitting"
          @click="handleSubmit"
        >
          登录后台
        </el-button>
      </el-form>
    </section>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
}

.login-card {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  width: min(1080px, 100%);
  overflow: hidden;
  border: 1px solid rgba(112, 84, 33, 0.12);
  border-radius: 32px;
  background: rgba(255, 253, 248, 0.88);
  box-shadow: 0 32px 80px rgba(89, 66, 28, 0.16);
}

.login-copy {
  padding: 52px 48px;
  background:
    radial-gradient(circle at top left, rgba(246, 205, 121, 0.2), transparent 36%),
    linear-gradient(135deg, rgba(49, 39, 26, 0.96), rgba(31, 26, 19, 0.98));
  color: #f6eddc;
}

.eyebrow {
  margin: 0 0 12px;
  color: #f2c879;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.26em;
  text-transform: uppercase;
}

.login-copy h1 {
  margin: 0;
  font-size: 52px;
  line-height: 1.08;
}

.summary {
  max-width: 420px;
  margin: 20px 0 0;
  color: rgba(246, 237, 220, 0.82);
  font-size: 16px;
  line-height: 1.85;
  white-space: pre-line;
}

.login-form {
  padding: 48px 40px;
}

.login-button {
  width: 100%;
  margin-top: 12px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(135deg, #342514, #8d6428);
}
</style>

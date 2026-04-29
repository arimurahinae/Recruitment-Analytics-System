<template>
  <div class="auth-page">
    <el-card class="auth-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>用户登录</span>
        </div>
      </template>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            clearable
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
            clearable
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            style="width: 100%"
            :loading="loading"
            @click="onSubmit"
          >
            登录
          </el-button>
        </el-form-item>
        <div class="footer-link">
          还没有账号？
          <router-link to="/register">去注册</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { loginApi } from "@/api/auth";

const router = useRouter();
const route = useRoute();

const formRef = ref();
const loading = ref(false);

const form = reactive({
  username: "",
  password: "",
});

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
};

onMounted(() => {
  const u = route.query.u;
  if (typeof u === "string" && u) {
    form.username = u;
  }
});

async function onSubmit() {
  const valid = await formRef.value
    ?.validate()
    .then(() => true)
    .catch(() => false);
  if (!valid) return;

  loading.value = true;
  try {
    const data = await loginApi({
      username: form.username.trim(),
      password: form.password,
    });
    if (data?.ok && data?.token) {
      localStorage.setItem("auth_token", data.token);
      localStorage.setItem("auth_user", JSON.stringify(data.user || {}));
      ElMessage.success("登录成功");
      const redirect = route.query.redirect || "/workspace";
      router.replace(typeof redirect === "string" ? redirect : "/workspace");
    } else {
      ElMessage.error(
        data?.message ||
          "登录未成功：请确认 Django 已启动且前端 /api 代理正确（勿用 file:// 打开页面）"
      );
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #0f1419 0%, #1a2332 45%, #0d1117 100%);
  padding: 24px;
  box-sizing: border-box;
}
.auth-card {
  width: 100%;
  max-width: 420px;
  --el-card-bg-color: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-darker);
}
.card-header {
  font-weight: 600;
  font-size: 18px;
  color: var(--el-text-color-primary);
}
.footer-link {
  text-align: center;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}
.footer-link a {
  color: var(--el-color-primary-light-3);
  text-decoration: none;
}
.footer-link a:hover {
  color: var(--el-color-primary);
  text-decoration: underline;
}
</style>

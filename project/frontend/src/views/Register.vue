<template>
  <div class="auth-page">
    <el-card class="auth-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>用户注册</span>
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
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="设置登录密码"
            show-password
            clearable
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="password2">
          <el-input
            v-model="form.password2"
            type="password"
            placeholder="再次输入密码"
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
            注册
          </el-button>
        </el-form-item>
        <div class="footer-link">
          已有账号？
          <router-link to="/login">去登录</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { registerApi } from "@/api/auth";

const router = useRouter();
const formRef = ref();
const loading = ref(false);

const form = reactive({
  username: "",
  password: "",
  password2: "",
});

function validatePass2(_rule, value, callback) {
  if (value !== form.password) {
    callback(new Error("两次输入的密码不一致"));
  } else {
    callback();
  }
}

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
  password2: [
    { required: true, message: "请确认密码", trigger: "blur" },
    { validator: validatePass2, trigger: "blur" },
  ],
};

async function onSubmit() {
  const valid = await formRef.value
    ?.validate()
    .then(() => true)
    .catch(() => false);
  if (!valid) return;

  loading.value = true;
  try {
    const data = await registerApi({
      username: form.username.trim(),
      password: form.password,
    });
    if (data?.ok) {
      ElMessage.success(data.message || "注册成功，请登录");
      router.replace({
        path: "/login",
        query: { u: form.username.trim() },
      });
    } else {
      ElMessage.error(
        data?.message ||
          "注册未成功：请确认本机已运行 Django（8000），且前端已代理 /api"
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
  background: linear-gradient(145deg, #0d1117 0%, #161b22 50%, #0f1419 100%);
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

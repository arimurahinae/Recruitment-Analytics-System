<template>
  <div class="workspace-shell">
    <el-container class="workspace-root">
      <el-header class="ws-header" height="56px">
        <div class="ws-header__brand">
          <span class="ws-logo">招聘数据</span>
          <span class="ws-sub">管理后台</span>
        </div>
        <div class="ws-header__right">
          <el-avatar :size="30" :src="user.avatar || ''">
            <span v-if="!user.avatar">{{ usernameInitials }}</span>
          </el-avatar>
          <span class="ws-username">{{ username }}</span>
          <el-button type="primary" link @click="logout">退出登录</el-button>
        </div>
      </el-header>
      <el-container class="ws-body">
        <el-aside class="ws-aside" width="220px">
          <el-menu
            class="ws-menu"
            :router="true"
            :default-active="route.path"
            background-color="transparent"
          >
            <el-menu-item index="/bigscreen">
              <el-icon><Monitor /></el-icon>
              <span>数据可视化大屏</span>
            </el-menu-item>
            <el-menu-item index="/workspace">
              <el-icon><DataAnalysis /></el-icon>
              <span>系统首页</span>
            </el-menu-item>
            <el-menu-item index="/workspace/jobs">
              <el-icon><Tickets /></el-icon>
              <span>岗位表格</span>
            </el-menu-item>
            <el-menu-item index="/workspace/salary-predict">
              <el-icon><TrendCharts /></el-icon>
              <span>薪资预测</span>
            </el-menu-item>
            <el-menu-item index="/workspace/profile">
              <el-icon><User /></el-icon>
              <span>个人信息</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main class="ws-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { DataAnalysis, Monitor, Tickets, TrendCharts, User } from "@element-plus/icons-vue";
import { useCurrentUser } from "@/composables/useCurrentUser";

const route = useRoute();
const router = useRouter();
const { user } = useCurrentUser();

const username = computed(() => user.username || "—");
const usernameInitials = computed(() => (user.username || "用").slice(0, 2).toUpperCase());

function logout() {
  localStorage.removeItem("auth_token");
  localStorage.removeItem("auth_user");
  router.replace("/login");
}
</script>

<style scoped>
.workspace-shell {
  --ws-bg-page: #e8f4fc;
  --ws-bg-card: #ffffff;
  --ws-border: #b3d9f2;
  --ws-header-bg: linear-gradient(180deg, #d6ebfa 0%, #cfe8f8 100%);
  --ws-aside-bg: #dceef9;
  --ws-text: #1a4a6e;
  --ws-text-dim: #5a7a94;
  --ws-primary: #2b8ccb;
  --ws-menu-active: #e3f4ff;

  min-height: 100%;
  background: var(--ws-bg-page);
  color: var(--ws-text);
}

.workspace-root {
  min-height: 100vh;
  flex-direction: column;
}

.ws-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: var(--ws-header-bg);
  border-bottom: 1px solid var(--ws-border);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.8) inset;
}

.ws-header__brand {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.ws-logo {
  font-size: 18px;
  font-weight: 700;
  color: var(--ws-primary);
}

.ws-sub {
  font-size: 13px;
  color: var(--ws-text-dim);
}

.ws-header__right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.ws-username {
  font-size: 14px;
  color: var(--ws-text);
  font-weight: 500;
}

.ws-body {
  flex: 1;
  min-height: 0;
}

.ws-aside {
  background: var(--ws-aside-bg);
  border-right: 1px solid var(--ws-border);
  padding: 12px 0;
}

.ws-menu {
  border-right: none;
}

.ws-menu :deep(.el-menu-item) {
  color: var(--ws-text);
}

.ws-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.45) !important;
}

.ws-menu :deep(.el-menu-item.is-active) {
  color: var(--ws-primary);
  background: var(--ws-menu-active) !important;
  font-weight: 600;
}

.ws-main {
  padding: 16px 20px 24px;
  background: var(--ws-bg-page);
  overflow: auto;
}
</style>

<template>
  <el-container class="home">
    <el-header class="header">
      <span class="title">招聘系统</span>
      <div class="actions">
        <span v-if="userLabel" class="user-label">{{ userLabel }}</span>
        <el-button type="primary" link @click="logout">退出登录</el-button>
      </div>
    </el-header>
    <el-main>
      <el-card>
        <template #header>词云示例（ECharts + echarts-wordcloud）</template>
        <div ref="chartRef" class="chart-box" />
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import * as echarts from "echarts";
import "echarts-wordcloud";
import { useCurrentUser } from "@/composables/useCurrentUser";

const router = useRouter();

const { user } = useCurrentUser();
const chartRef = ref(null);
let chart;

const userLabel = computed(() => (user.username ? `你好，${user.username}` : ""));

function logout() {
  localStorage.removeItem("auth_token");
  localStorage.removeItem("auth_user");
  router.replace("/login");
}

function initWordCloud() {
  if (!chartRef.value) return;
  chart = echarts.init(chartRef.value, "dark");
  const demo = [
    { name: "Python", value: 80 },
    { name: "Vue", value: 70 },
    { name: "Django", value: 65 },
    { name: "MySQL", value: 60 },
    { name: "招聘", value: 90 },
    { name: "数据分析", value: 55 },
    { name: "前端", value: 75 },
    { name: "后端", value: 72 },
  ];
  chart.setOption({
    backgroundColor: "transparent",
    series: [
      {
        type: "wordCloud",
        shape: "circle",
        left: "center",
        top: "center",
        width: "100%",
        height: "100%",
        sizeRange: [14, 48],
        rotationRange: [-45, 45],
        gridSize: 8,
        textStyle: {
          color() {
            const base = 120 + Math.round(Math.random() * 135);
            const g = 140 + Math.round(Math.random() * 80);
            const b = 200 + Math.round(Math.random() * 55);
            return `rgb(${base}, ${g}, ${b})`;
          },
        },
        data: demo,
      },
    ],
  });
}

onMounted(() => {
  initWordCloud();
  window.addEventListener("resize", resize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resize);
  chart?.dispose();
});

function resize() {
  chart?.resize();
}
</script>

<style scoped>
.home {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  height: 56px !important;
}
.title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-label {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
:deep(.el-main) {
  background: var(--el-bg-color-page);
}
:deep(.el-card) {
  --el-card-bg-color: var(--el-bg-color-overlay);
  border-color: var(--el-border-color-darker);
}
.chart-box {
  width: 100%;
  height: 360px;
}
</style>

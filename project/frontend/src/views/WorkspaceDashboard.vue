<template>
  <div class="ws-dash">
    <div class="ws-dash__head">
      <h1 class="ws-dash__title">系统首页</h1>
      <p class="ws-dash__desc">

      </p>
    </div>

    <el-alert
      v-if="loadError"
      type="error"
      :closable="false"
      show-icon
      :title="loadError"
      class="ws-dash__alert"
    />

    <el-row v-if="!loadError" :gutter="14" class="ws-dash__stats">
      <el-col v-for="c in statCards" :key="c.key" :xs="24" :sm="12" :md="8" :lg="6" :xl="4">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card__label">{{ c.label }}</div>
          <div class="stat-card__value">{{ c.display }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="!loadError" class="ws-dash__section" shadow="never">
      <template #header>
        <span class="section-title">高薪岗位 TOP（薪资区间优先）</span>
      </template>
      <el-table
        :data="salaryJobRows"
        stripe
        border
        size="small"
        max-height="360"
        empty-text="暂无数据"
        class="ws-table"
      >
        <el-table-column type="index" label="#" width="48" />
        <el-table-column prop="job_title" label="岗位标题" min-width="160" show-overflow-tooltip />
        <el-table-column prop="company_name" label="公司" min-width="120" show-overflow-tooltip />
        <el-table-column prop="query_city_name" label="城市" width="88" />
        <el-table-column prop="job_salary" label="薪资(文本)" width="110" show-overflow-tooltip />
        <el-table-column label="上限(K)" width="80" align="right">
          <template #default="{ row }">{{ row.salary_max ?? row.salary_min ?? "—" }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-row v-if="!loadError" :gutter="14" class="ws-dash__charts">
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="chart-card">
          <template #header><span class="section-title">热门岗位标题 TOP10</span></template>
          <div ref="refTitles" class="chart-box chart-box--hbar" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="chart-card">
          <template #header><span class="section-title">行业结构环状图</span></template>
          <div ref="refIndustryRing" class="chart-box chart-box--ring" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="chart-card">
          <template #header><span class="section-title">省级岗位分布 TOP12</span></template>
          <div ref="refProvince" class="chart-box chart-box--hbar" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="chart-card">
          <template #header><span class="section-title">招聘岗位数 · 公司 TOP10</span></template>
          <div ref="refCompanies" class="chart-box chart-box--hbar" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="24">
        <el-card shadow="never" class="chart-card">
          <template #header><span class="section-title">工作经验画像图</span></template>
          <div ref="refWorkProfile" class="chart-box chart-box--wide" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts";
import { fetchJobDashboard } from "@/api/job";

const W = {
  primary: "#2b8ccb",
  secondary: "#5cb3e0",
  accent: "#7ec8e3",
  text: "#1a4a6e",
  textDim: "#5a7a94",
  axis: "#94b8d4",
  split: "rgba(43, 140, 203, 0.12)",
};

const payload = ref(null);
const loadError = ref("");
const refTitles = ref(null);
const refIndustryRing = ref(null);
const refProvince = ref(null);
const refCompanies = ref(null);
const refWorkProfile = ref(null);

let chartTitles;
let chartIndustryRing;
let chartProvince;
let chartCompanies;
let chartWorkProfile;

function truncLabel(s, n = 18) {
  const t = String(s ?? "");
  return t.length > n ? `${t.slice(0, n - 1)}…` : t;
}

const statCards = computed(() => {
  const s = payload.value?.summary;
  if (!s) {
    return [
      { key: "j", label: "岗位总数", display: "—" },
      { key: "c", label: "关联公司数", display: "—" },
      { key: "ct", label: "库内公司总数", display: "—" },
      { key: "ws", label: "有薪资岗位数", display: "—" },
      { key: "t", label: "置顶岗位", display: "—" },
      { key: "city", label: "覆盖城市", display: "—" },
    ];
  }
  return [
    { key: "j", label: "岗位总数", display: String(s.total_jobs ?? 0) },
    { key: "c", label: "关联公司数", display: String(s.companies_in_jobs ?? 0) },
    { key: "ct", label: "库内公司总数", display: String(s.companies_total ?? 0) },
    { key: "ws", label: "有薪资岗位数", display: String(s.jobs_with_salary ?? 0) },
    { key: "t", label: "置顶岗位", display: String(s.top_job_count ?? 0) },
    { key: "city", label: "覆盖城市", display: String(s.city_count ?? 0) },
  ];
});

const salaryJobRows = computed(() => payload.value?.top_salary_jobs || []);

function baseOpt() {
  return {
    textStyle: { fontFamily: "Microsoft YaHei, PingFang SC, sans-serif", color: W.text },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: "#fff",
      borderColor: W.axis,
      textStyle: { color: W.text },
    },
  };
}

function initHBar(el, rows, color, { gridRight = 52 } = {}) {
  if (!el) return null;
  const chart = echarts.init(el, null, { renderer: "canvas" });
  const d = [...rows].sort((a, b) => (b.value || 0) - (a.value || 0));
  if (!d.length) {
    chart.setOption({
      ...baseOpt(),
      title: {
        text: "暂无数据",
        left: "center",
        top: "center",
        textStyle: { color: W.textDim, fontSize: 14 },
      },
    });
    return chart;
  }
  chart.setOption({
    ...baseOpt(),
    grid: { left: 8, right: gridRight, top: 8, bottom: 8, containLabel: true },
    xAxis: {
      type: "value",
      axisLabel: { color: W.textDim, fontSize: 11 },
      splitLine: { lineStyle: { color: W.split } },
    },
    yAxis: {
      type: "category",
      data: d.map((x) => truncLabel(x.name, 20)),
      inverse: true,
      axisLabel: { color: W.text, fontSize: 11 },
      axisLine: { lineStyle: { color: W.axis } },
    },
    series: [
      {
        type: "bar",
        data: d.map((x) => x.value),
        barMaxWidth: 20,
        itemStyle: { color },
        label: { show: true, position: "right", color: W.textDim, fontSize: 10 },
      },
    ],
  });
  return chart;
}

function initTopTitles() {
  chartTitles?.dispose();
  const list = (payload.value?.top_titles || []).slice(0, 10);
  chartTitles = initHBar(refTitles.value, list, W.primary, { gridRight: 48 });
}

function initIndustryRing() {
  chartIndustryRing?.dispose();
  const chart = echarts.init(refIndustryRing.value, null, { renderer: "canvas" });
  const list = (payload.value?.by_industry || []).slice(0, 10);
  if (!list.length) {
    chart.setOption({
      ...baseOpt(),
      title: {
        text: "暂无行业数据",
        left: "center",
        top: "center",
        textStyle: { color: W.textDim, fontSize: 14 },
      },
    });
    chartIndustryRing = chart;
    return;
  }
  chart.setOption({
    ...baseOpt(),
    tooltip: { trigger: "item" },
    legend: {
      type: "scroll",
      orient: "vertical",
      right: 8,
      top: "middle",
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: W.textDim, fontSize: 11 },
      formatter: (name) => truncLabel(name, 9),
    },
    series: [
      {
        name: "行业结构",
        type: "pie",
        radius: ["42%", "66%"],
        center: ["38%", "50%"],
        avoidLabelOverlap: true,
        label: { color: W.text, fontSize: 11, formatter: "{d}%" },
        labelLine: { length: 8, length2: 6 },
        data: list,
        itemStyle: { borderColor: "#fff", borderWidth: 2 },
        color: [W.primary, W.secondary, W.accent, "#8ecae6", "#a8d8ea", "#9bc5de", "#6fb3d8", "#7fb8e6"],
      },
    ],
  });
  chartIndustryRing = chart;
}

function initProvince() {
  chartProvince?.dispose();
  const list = (payload.value?.by_province || []).slice(0, 12);
  const chart = echarts.init(refProvince.value, null, { renderer: "canvas" });
  if (!list.length) {
    chart.setOption({
      ...baseOpt(),
      title: {
        text: "暂无省级数据",
        left: "center",
        top: "center",
        textStyle: { color: W.textDim, fontSize: 14 },
      },
    });
    chartProvince = chart;
    return;
  }
  chart.setOption({
    ...baseOpt(),
    grid: { left: 40, right: 16, top: 26, bottom: 40, containLabel: false },
    xAxis: {
      type: "category",
      data: list.map((x) => truncLabel(x.name, 6)),
      axisLabel: { color: W.textDim, fontSize: 11, rotate: 30 },
      axisLine: { lineStyle: { color: W.axis } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: W.textDim, fontSize: 11 },
      splitLine: { lineStyle: { color: W.split } },
    },
    series: [
      {
        type: "line",
        smooth: true,
        data: list.map((x) => x.value),
        areaStyle: { color: "rgba(43, 140, 203, 0.18)" },
        lineStyle: { color: W.primary, width: 2 },
        itemStyle: { color: W.secondary },
      },
    ],
  });
  chartProvince = chart;
}

function initCompanies() {
  chartCompanies?.dispose();
  const list = (payload.value?.top_companies || []).slice(0, 6);
  const chart = echarts.init(refCompanies.value, null, { renderer: "canvas" });
  if (!list.length) {
    chart.setOption({
      ...baseOpt(),
      title: {
        text: "暂无公司数据",
        left: "center",
        top: "center",
        textStyle: { color: W.textDim, fontSize: 14 },
      },
    });
    chartCompanies = chart;
    return;
  }
  const maxVal = Math.max(...list.map((x) => x.value || 0), 1);
  chart.setOption({
    ...baseOpt(),
    tooltip: { trigger: "item" },
    radar: {
      radius: "65%",
      center: ["50%", "52%"],
      splitNumber: 4,
      indicator: list.map((x) => ({
        name: truncLabel(x.name, 8),
        max: Math.ceil(maxVal * 1.1),
      })),
      axisName: { color: W.textDim, fontSize: 11 },
      splitLine: { lineStyle: { color: W.split } },
      splitArea: { areaStyle: { color: ["rgba(91, 179, 233, 0.08)", "rgba(43, 140, 203, 0.02)"] } },
      axisLine: { lineStyle: { color: W.axis } },
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: list.map((x) => x.value),
            name: "岗位数",
            areaStyle: { color: "rgba(43, 140, 203, 0.25)" },
            lineStyle: { color: W.accent, width: 2 },
            itemStyle: { color: W.accent },
          },
        ],
      },
    ],
  });
  chartCompanies = chart;
}

function initWorkProfile() {
  chartWorkProfile?.dispose();
  const list = (payload.value?.by_work_years || []).slice(0, 10);
  const chart = echarts.init(refWorkProfile.value, null, { renderer: "canvas" });
  if (!list.length) {
    chart.setOption({
      ...baseOpt(),
      title: {
        text: "暂无工作经验数据",
        left: "center",
        top: "center",
        textStyle: { color: W.textDim, fontSize: 14 },
      },
    });
    chartWorkProfile = chart;
    return;
  }
  chart.setOption({
    ...baseOpt(),
    tooltip: { trigger: "item" },
    legend: {
      type: "scroll",
      bottom: 8,
      left: "center",
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: W.textDim, fontSize: 11 },
    },
    series: [
      {
        name: "工作经验",
        type: "pie",
        radius: ["38%", "62%"],
        center: ["50%", "46%"],
        data: list,
        label: { color: W.text, fontSize: 11, formatter: "{b}\n{d}%" },
        labelLine: { length: 8, length2: 6 },
        itemStyle: { borderColor: "#fff", borderWidth: 2 },
        color: [W.primary, W.secondary, W.accent, "#8ecae6", "#a8d8ea", "#9bc5de"],
      },
    ],
  });
  chartWorkProfile = chart;
}

function resizeAll() {
  [chartTitles, chartIndustryRing, chartProvince, chartCompanies, chartWorkProfile].forEach((c) => c?.resize());
}

function disposeAll() {
  [chartTitles, chartIndustryRing, chartProvince, chartCompanies, chartWorkProfile].forEach((c) => c?.dispose());
  chartTitles = chartIndustryRing = chartProvince = chartCompanies = chartWorkProfile = null;
}

async function load() {
  loadError.value = "";
  try {
    const data = await fetchJobDashboard();
    if (!data?.ok) {
      loadError.value = data?.message || "加载失败";
      return;
    }
    payload.value = data;
    await nextTick();
    initTopTitles();
    initIndustryRing();
    initProvince();
    initCompanies();
    initWorkProfile();
    resizeAll();
  } catch (e) {
    loadError.value = e?.message || String(e);
  }
}

onMounted(() => {
  load();
  window.addEventListener("resize", resizeAll);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeAll);
  disposeAll();
});
</script>

<style scoped>
.ws-dash {
  max-width: 1400px;
  margin: 0 auto;
}

.ws-dash__head {
  margin-bottom: 16px;
}

.ws-dash__title {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 700;
  color: #1a4a6e;
}

.ws-dash__desc {
  margin: 0;
  font-size: 13px;
  color: #5a7a94;
  line-height: 1.55;
}

.ws-dash__alert {
  margin-bottom: 16px;
}

.ws-dash__stats {
  margin-bottom: 16px;
}

.stat-card {
  border-radius: 10px;
  border: 1px solid #b3d9f2;
  background: linear-gradient(180deg, #ffffff 0%, #f5fbff 100%);
  margin-bottom: 14px;
}

.stat-card :deep(.el-card__body) {
  padding: 14px 16px;
}

.stat-card__label {
  font-size: 12px;
  color: #5a7a94;
  margin-bottom: 6px;
}

.stat-card__value {
  font-size: 22px;
  font-weight: 700;
  color: #2b8ccb;
  font-variant-numeric: tabular-nums;
}

.ws-dash__section {
  margin-bottom: 16px;
  border-radius: 10px;
  border: 1px solid #b3d9f2;
  background: #fff;
}

.section-title {
  font-weight: 600;
  color: #1a4a6e;
  font-size: 15px;
}

.ws-table {
  width: 100%;
}

.ws-dash__charts {
  margin-bottom: 8px;
}

.chart-card {
  margin-bottom: 14px;
  border-radius: 10px;
  border: 1px solid #b3d9f2;
  background: #fff;
}

.chart-box {
  width: 100%;
}

.chart-box--hbar {
  height: 320px;
}

.chart-box--ring {
  height: 320px;
}

.chart-box--wide {
  height: 340px;
}
</style>

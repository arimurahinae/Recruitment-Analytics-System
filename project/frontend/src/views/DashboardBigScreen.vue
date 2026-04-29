<template>
  <div class="bigscreen">
    <header class="bs-header">
      <div class="bs-header__left">
        <h1 class="bs-title">招聘数据可视化大屏</h1>
        <span class="bs-sub">岗位数据监控分析</span>
      </div>
      <nav class="bs-header__nav">
        <button type="button" class="bs-nav-link" @click="goWorkspace">系统首页</button>
        <span class="nav-item">总览</span>
        <span class="nav-item">岗位</span>
        <span class="nav-item">地域</span>
        <span class="nav-item">行业</span>
      </nav>
      <div class="bs-header__right">
        <div class="bs-user-wrap">
          <img v-if="user.avatar" :src="user.avatar" class="bs-avatar" :alt="username" />
          <div v-else class="bs-avatar bs-avatar--placeholder">{{ userInitials }}</div>
          <span class="bs-user">{{ username }}</span>
        </div>
        <span class="clock">{{ clockText }}</span>
        <button type="button" class="bs-btn" @click="goWorkspace">进入后台</button>
        <button type="button" class="bs-btn bs-btn--primary" @click="logout">退出</button>
      </div>
    </header>

    <div v-if="loadError" class="bs-error">{{ loadError }}</div>

    <div v-else class="bs-scroll">
      <div class="bs-main">
      <aside class="bs-col bs-col--left">
        <section class="panel">
          <div class="panel__title"><span class="panel__title-text">城市岗位 TOP</span></div>
          <div ref="refCityTable" class="panel__chart panel__chart--table">
            <table v-if="payload?.by_city?.length" class="data-table">
              <thead>
                <tr>
                  <th>城市</th>
                  <th>岗位数</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r, i) in payload.by_city.slice(0, 8)" :key="i">
                  <td>{{ r.name }}</td>
                  <td class="num">{{ r.value }}</td>
                </tr>
              </tbody>
            </table>
            <p v-else class="empty-hint">暂无数据</p>
          </div>
        </section>
        <section class="panel panel--grow">
          <div class="panel__title"><span class="panel__title-text">薪资最高 TOP5</span></div>
          <div class="panel__chart panel__chart--top-salary">
            <ul v-if="topSalaryJobs.length" class="top-salary-list">
              <li v-for="(row, idx) in topSalaryJobs" :key="row.job_jobId" class="top-salary-row">
                <img
                  v-if="topSalaryLogoUrl(row)"
                  :src="topSalaryLogoUrl(row)"
                  :alt="row.company_name || row.job_title || '岗位'"
                  class="top-salary-thumb top-salary-thumb--img"
                  loading="lazy"
                />
                <div v-else class="top-salary-thumb" aria-hidden="true" />
                <div class="top-salary-body">
                  <span class="top-salary-rank">{{ idx + 1 }}</span>
                  <div class="top-salary-info">
                    <div class="top-salary-title">{{ row.job_title }}</div>
                    <div class="top-salary-meta">{{ topSalaryMeta(row) }}</div>
                  </div>
                  <div class="top-salary-money">{{ formatTopSalary(row) }}</div>
                </div>
              </li>
            </ul>
            <p v-else class="empty-hint">暂无有效薪资区间的岗位</p>
          </div>
        </section>
      </aside>

      <main class="bs-col bs-col--center">
        <div class="kpi-row">
          <div v-for="k in kpiList" :key="k.key" class="kpi-card">
            <div class="kpi-card__label">{{ k.label }}</div>
            <div class="kpi-card__value">{{ k.display }}</div>
          </div>
        </div>
        <section class="panel panel--map">
          <div class="panel__title">
            <span class="panel__title-text">全国岗位分布</span>
            <span class="panel__title-hint">可缩放拖拽 · 颜色为各省岗位量</span>
          </div>
          <div ref="refMap" class="panel__chart panel__chart--map" />
        </section>
        <section style="height: 260px" class="panel">
          <div class="panel__title"><span class="panel__title-text">岗位刷新月度趋势</span></div>
          <div ref="refLine" class="panel__chart panel__chart--line" />
        </section>
      </main>

      <aside class="bs-col bs-col--right">
        <section class="panel panel--industry">
          <div class="panel__title"><span class="panel__title-text">公司行业分布</span></div>
          <div ref="refIndustry" class="panel__chart panel__chart--industry" />
        </section>
        <section class="panel panel--grow">
          <div class="panel__title">
            <span class="panel__title-text">热门标签 / 岗位名 TOP</span>
          </div>
          <div ref="refWord" class="panel__chart" />
        </section>
      </aside>
      </div>

      <footer class="bs-footer">
      <section class="panel panel--footer">
        <div class="panel__title"><span class="panel__title-text">学历要求</span></div>
        <div ref="refEdu" class="panel__chart panel__chart--footer" />
      </section>
      <section class="panel panel--footer">
        <div class="panel__title"><span class="panel__title-text">工作年限</span></div>
        <div ref="refWork" class="panel__chart panel__chart--footer panel__chart--work-years" />
      </section>
      <section class="panel panel--footer">
        <div class="panel__title"><span class="panel__title-text">月薪区间 (K)</span></div>
        <div ref="refSalary" class="panel__chart panel__chart--footer" />
      </section>
      <section class="panel panel--footer">
        <div class="panel__title"><span class="panel__title-text">岗位类型</span></div>
        <div ref="refKind" class="panel__chart panel__chart--footer" />
      </section>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import * as echarts from "echarts";
import { fetchJobDashboard } from "@/api/job";
import { cityToScatterData } from "@/utils/cityCoords";
import { useCurrentUser } from "@/composables/useCurrentUser";

const router = useRouter();
const { user } = useCurrentUser();

const C = {
  primary: "#00f0ff",
  secondary: "#00ffa6",
  accent: "#ffd54f",
  danger: "#ff4d4f",
  text: "rgba(255,255,255,0.75)",
  textDim: "rgba(255,255,255,0.45)",
  axis: "rgba(255,255,255,0.25)",
  split: "rgba(255,255,255,0.08)",
  panel: "#0b2a4a",
};

const payload = ref(null);
const loadError = ref("");
const clockText = ref("");

const refMap = ref(null);
const refLine = ref(null);
const refIndustry = ref(null);
const refWord = ref(null);
const refEdu = ref(null);
const refWork = ref(null);
const refSalary = ref(null);
const refKind = ref(null);

let chartMap;
let chartLine;
let chartIndustry;
let chartWord;
let chartEdu;
let chartWork;
let chartSalary;
let chartKind;
let mapRegistered = false;
let chinaMapScriptPromise = null;
let clockTimer;

const kpiList = computed(() => {
  const s = payload.value?.summary;
  if (!s) {
    return [
      { key: "j", label: "岗位总数", display: "—" },
      { key: "c", label: "关联公司数", display: "—" },
      { key: "a", label: "平均月薪下限(K)", display: "—" },
      { key: "t", label: "置顶岗位", display: "—" },
      { key: "city", label: "覆盖城市", display: "—" },
    ];
  }
  return [
    { key: "j", label: "岗位总数", display: String(s.total_jobs ?? 0) },
    { key: "c", label: "关联公司数", display: String(s.companies_in_jobs ?? 0) },
    {
      key: "a",
      label: "平均月薪下限(K)",
      display: s.avg_salary_min_k != null ? String(s.avg_salary_min_k) : "—",
    },
    { key: "t", label: "置顶岗位", display: String(s.top_job_count ?? 0) },
    { key: "city", label: "覆盖城市", display: String(s.city_count ?? 0) },
  ];
});

const topSalaryJobs = computed(() => payload.value?.top_salary_jobs || []);

function formatTopSalary(row) {
  if (row?.job_salary && String(row.job_salary).trim()) return String(row.job_salary).trim();
  const a = row?.salary_min;
  const b = row?.salary_max;
  if (a != null && b != null) return `${a}-${b}K`;
  if (b != null) return `最高 ${b}K`;
  if (a != null) return `${a}K起`;
  return "—";
}

function topSalaryMeta(row) {
  const co = row?.company_name || "";
  const city = row?.query_city_name || "";
  if (co && city) return `${co} · ${city}`;
  return co || city || "—";
}

/** 猎聘白底 222 缩略图：库中可能为 image0.liepin.com/xxx.png，统一规范为 lietou-static 的 bg_white_222x222 路径 */
const LIEPIN_LOGO_BASE = "https://image0.lietou-static.com/bg_white_222x222/";

function topSalaryLogoUrl(row) {
  const raw = (row?.company_logo || "").trim();
  if (!raw) return "";
  let name = "";
  if (/^https?:\/\//i.test(raw)) {
    try {
      const u = new URL(raw);
      name = u.pathname.split("/").filter(Boolean).pop() || "";
    } catch {
      name = raw.split("/").pop()?.split("?")[0] || "";
    }
  } else {
    name = raw.replace(/^\/+/, "").split("/").pop() || raw;
  }
  if (!name) return "";
  const file = /\.(png|jpe?g|gif|webp)$/i.test(name) ? name : `${name}.png`;
  return LIEPIN_LOGO_BASE + file;
}

function tickClock() {
  const d = new Date();
  clockText.value = `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}:${String(d.getSeconds()).padStart(2, "0")}`;
}

function logout() {
  localStorage.removeItem("auth_token");
  localStorage.removeItem("auth_user");
  router.replace("/login");
}

function goWorkspace() {
  router.push("/workspace");
}

const username = computed(() => user.username || "用户");

const userInitials = computed(() =>
  String(user.username || "用户").slice(0, 2).toUpperCase()
);

/** 优先加载项目 public/china.js（与 echarts 同源实例注册），失败再回退 CDN GeoJSON */
async function tryRegisterChinaMap() {
  if (mapRegistered) return true;
  try {
    if (typeof echarts.getMap === "function" && echarts.getMap("china")) {
      mapRegistered = true;
      return true;
    }
  } catch {
    /* 忽略 */
  }

  if (!chinaMapScriptPromise) {
    chinaMapScriptPromise = new Promise((resolve) => {
      if (document.querySelector("script[data-china-map='1']")) {
        resolve(typeof echarts.getMap === "function" && !!echarts.getMap("china"));
        return;
      }
      const w = window;
      const prev = w.echarts;
      w.echarts = echarts;
      const s = document.createElement("script");
      s.src = `${import.meta.env.BASE_URL}china.js`;
      s.async = true;
      s.dataset.chinaMap = "1";
      s.onload = () => {
        const ok = typeof echarts.getMap === "function" && !!echarts.getMap("china");
        if (prev !== undefined) w.echarts = prev;
        else delete w.echarts;
        resolve(ok);
      };
      s.onerror = () => {
        if (prev !== undefined) w.echarts = prev;
        else delete w.echarts;
        resolve(false);
      };
      document.head.appendChild(s);
    });
  }

  let ok = await chinaMapScriptPromise;
  if (ok) {
    mapRegistered = true;
    return true;
  }

  try {
    const url = "https://cdn.jsdelivr.net/npm/echarts@5.4.3/map/json/china.json";
    const res = await fetch(url);
    if (!res.ok) return false;
    const geo = await res.json();
    echarts.registerMap("china", geo);
    mapRegistered = true;
    return true;
  } catch {
    return false;
  }
}

function baseChartOptions() {
  return {
    textStyle: { fontFamily: "Microsoft YaHei, PingFang SC, sans-serif" },
    tooltip: {
      backgroundColor: C.panel,
      borderColor: C.primary,
      textStyle: { color: "#fff" },
    },
  };
}

function initMap(hasGeo) {
  if (!refMap.value) return;
  chartMap?.dispose();
  chartMap = echarts.init(refMap.value, null, { renderer: "canvas" });
  const byCity = payload.value?.by_city || [];
  const byProvince = payload.value?.by_province || [];
  const scatter = cityToScatterData(byCity);

  if (hasGeo) {
    const provMax = Math.max(...byProvince.map((p) => p.value || 0), 1);
    const hints = [];
    if (!byCity.length) hints.push("暂无城市岗位数据");
    else if (!byProvince.length) hints.push("城市未能匹配到省级区划，请在后端扩展 city_province 映射");
    if (byCity.length && !scatter.length) hints.push("部分城市无经纬度散点");
    const hint = hints.join(" · ");

    const series = [
      {
        name: "省级岗位",
        type: "map",
        geoIndex: 0,
        data: byProvince,
        tooltip: {
          formatter: (p) =>
            p.data != null && typeof p.value === "number"
              ? `${p.name}<br/>岗位数：${p.value}`
              : `${p.name}<br/>岗位数：0`,
        },
        emphasis: {
          label: { show: true, color: "#fff", fontSize: 11 },
          itemStyle: { areaColor: "rgba(255, 213, 79, 0.55)", borderColor: "#fff", borderWidth: 1 },
        },
        itemStyle: {
          borderColor: "rgba(30, 144, 255, 0.85)",
          borderWidth: 0.6,
        },
      },
    ];
    if (scatter.length) {
      series.push({
        name: "城市热力",
        type: "effectScatter",
        coordinateSystem: "geo",
        geoIndex: 0,
        data: scatter,
        symbolSize(val) {
          const v = val[2] || 0;
          return Math.min(30, 9 + Math.sqrt(v) * 2);
        },
        tooltip: {
          formatter: (p) => `${p.name}<br/>岗位数：${p.value?.[2] ?? p.value ?? "—"}`,
        },
        rippleEffect: { brushType: "stroke", color: C.accent },
        itemStyle: { color: C.accent, shadowBlur: 12, shadowColor: C.accent },
        zlevel: 2,
      });
    }

    chartMap.setOption({
      ...baseChartOptions(),
      tooltip: { trigger: "item" },
      visualMap: {
        type: "continuous",
        seriesIndex: 0,
        min: 0,
        max: provMax,
        left: 12,
        bottom: 48,
        text: ["多", "少"],
        textStyle: { color: C.textDim, fontSize: 10 },
        inRange: {
          color: ["#0a2544", "#0066aa", "#00c8ff", "#00ffa6"],
        },
        calculable: true,
      },
      geo: {
        map: "china",
        roam: true,
        scaleLimit: { min: 0.75, max: 12 },
        zoom: 1.05,
        layoutCenter: ["50%", "50%"],
        layoutSize: "90%",
        label: { show: false },
        itemStyle: {
          areaColor: "#0c2848",
          borderColor: "#2a6a9e",
          borderWidth: 0.5,
        },
        emphasis: { disabled: true },
      },
      graphic: hint
        ? [
            {
              type: "text",
              left: "center",
              bottom: "4%",
              style: {
                text: hint,
                fill: C.textDim,
                fontSize: 10,
              },
            },
          ]
        : [],
      series,
    });
    return;
  }

  const top = [...byCity].slice(0, 12);
  if (!top.length) {
    chartMap.setOption({
      ...baseChartOptions(),
      title: {
        text: "暂无城市分布数据",
        left: "center",
        top: "center",
        textStyle: { color: C.textDim, fontSize: 14 },
      },
    });
    return;
  }
  const topSorted = [...top].sort((a, b) => b.value - a.value);
  chartMap.setOption({
    ...baseChartOptions(),
    grid: {
      left: 4,
      right: 28,
      top: 10,
      bottom: 10,
      containLabel: true,
    },
    xAxis: {
      type: "value",
      axisLabel: { color: C.textDim, fontSize: 10 },
      splitLine: { lineStyle: { color: C.split } },
    },
    yAxis: {
      type: "category",
      data: topSorted.map((x) => x.name),
      inverse: true,
      axisLabel: {
        color: C.text,
        fontSize: 11,
        width: 96,
        overflow: "truncate",
        ellipsis: "…",
      },
      axisLine: { lineStyle: { color: C.axis } },
      axisTick: { alignWithLabel: true },
    },
    series: [
      {
        type: "bar",
        data: topSorted.map((x) => x.value),
        barMaxWidth: 20,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: "#00f0ff" },
            { offset: 1, color: "#00ffa6" },
          ]),
        },
      },
    ],
  });
}

function initLine() {
  if (!refLine.value) return;
  chartLine?.dispose();
  chartLine = echarts.init(refLine.value, null, { renderer: "canvas" });
  const bm = payload.value?.by_month || [];
  if (!bm.length) {
    chartLine.setOption({
      ...baseChartOptions(),
      title: {
        text: "暂无月度趋势数据",
        left: "center",
        top: "center",
        textStyle: { color: C.textDim, fontSize: 14 },
      },
    });
    return;
  }
  const n = bm.length;
  const monthStep = n <= 14 ? 1 : Math.max(2, Math.ceil(n / 12));
  chartLine.setOption({
    ...baseChartOptions(),
    grid: { left: 48, right: 20, bottom: 52, top: 28, containLabel: false },
    xAxis: {
      type: "category",
      data: bm.map((x) => x.month),
      axisLabel: {
        color: C.textDim,
        fontSize: 10,
        rotate: 38,
        interval: (idx) => idx % monthStep !== 0,
        hideOverlap: true,
      },
      axisLine: { lineStyle: { color: C.axis } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: C.textDim },
      splitLine: { lineStyle: { color: C.split } },
    },
    series: [
      {
        type: "line",
        smooth: true,
        data: bm.map((x) => x.value),
        areaStyle: { color: "rgba(0,240,255,0.15)" },
        lineStyle: { color: C.primary, width: 2 },
        itemStyle: { color: C.accent },
      },
    ],
  });
}

function initIndustry() {
  if (!refIndustry.value) return;
  chartIndustry?.dispose();
  chartIndustry = echarts.init(refIndustry.value, null, { renderer: "canvas" });
  const d = (payload.value?.by_industry || []).slice(0, 9);
  if (!d.length) {
    chartIndustry.setOption({
      ...baseChartOptions(),
      title: {
        text: "暂无行业数据",
        left: "center",
        top: "center",
        textStyle: { color: C.textDim, fontSize: 14 },
      },
    });
    return;
  }
  const maxIndustry = Math.max(...d.map((x) => x.value || 0), 1);
  const rough = maxIndustry / 4;
  const pow = 10 ** Math.floor(Math.log10(rough) || 0);
  const fr = rough / pow;
  const nf = fr <= 1 ? 1 : fr <= 2 ? 2 : fr <= 5 ? 5 : 10;
  const yStep = Math.max(1, nf * pow);
  const yMax = Math.ceil(maxIndustry / yStep) * yStep;
  chartIndustry.setOption({
    ...baseChartOptions(),
    grid: { left: 8, right: 10, bottom: 32, top: 10, containLabel: true },
    xAxis: {
      type: "category",
      data: d.map((x) => (x.name.length > 8 ? `${x.name.slice(0, 7)}…` : x.name)),
      axisLabel: {
        color: C.textDim,
        fontSize: 10,
        rotate: 28,
        interval: 0,
        hideOverlap: true,
      },
      axisLine: { lineStyle: { color: C.axis } },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: yMax,
      interval: yStep,
      axisLabel: {
        color: C.textDim,
        fontSize: 11,
        margin: 14,
        hideOverlap: true,
      },
      splitLine: { lineStyle: { color: C.split } },
    },
    series: [
      {
        type: "bar",
        data: d.map((x) => x.value),
        barWidth: "52%",
        itemStyle: { color: C.secondary },
      },
    ],
  });
}

function buildHotBarRows() {
  const acc = new Map();
  for (const w of payload.value?.wordcloud || []) {
    if (!w?.name) continue;
    acc.set(w.name, (acc.get(w.name) || 0) + (w.value || 0));
  }
  for (const t of payload.value?.top_titles || []) {
    if (!t?.name) continue;
    const key = t.name.length > 22 ? `${t.name.slice(0, 20)}…` : t.name;
    acc.set(key, (acc.get(key) || 0) + (t.value || 0));
  }
  const rows = [...acc.entries()]
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 15);
  return rows;
}

/** 词云数据稀疏时可读性差，统一用横向条形图展示标签 + 高频岗位名 */
function initHotTagsBar() {
  if (!refWord.value) return;
  chartWord?.dispose();
  chartWord = echarts.init(refWord.value, null, { renderer: "canvas" });
  const rows = buildHotBarRows();
  if (!rows.length) {
    chartWord.setOption({
      ...baseChartOptions(),
      title: {
        text: "暂无标签与标题样本",
        left: "center",
        top: "center",
        textStyle: { color: C.textDim, fontSize: 13 },
      },
    });
    return;
  }
  chartWord.setOption({
    ...baseChartOptions(),
    grid: { left: 4, right: 36, top: 8, bottom: 8, containLabel: true },
    xAxis: {
      type: "value",
      axisLabel: { color: C.textDim, fontSize: 10 },
      splitLine: { lineStyle: { color: C.split } },
    },
    yAxis: {
      type: "category",
      data: rows.map((r) => r.name),
      inverse: true,
      axisLabel: {
        color: C.text,
        fontSize: 10,
        width: 100,
        overflow: "truncate",
        ellipsis: "…",
      },
      axisLine: { lineStyle: { color: C.axis } },
    },
    series: [
      {
        type: "bar",
        data: rows.map((r) => r.value),
        barMaxWidth: 16,
        itemStyle: { color: C.secondary },
        label: {
          show: true,
          position: "right",
          color: C.accent,
          fontSize: 10,
        },
      },
    ],
  });
}

/**
 * @param {{ workLegend?: boolean }} [opts] workLegend：工作年限等类目较多时用语义 + 数量图例展示
 */
function initDonut(el, data, opts) {
  if (!el) return null;
  const chart = echarts.init(el, null, { renderer: "canvas" });
  const list = data.length ? data : [{ name: "无数据", value: 1 }];
  const workLegend = Boolean(opts?.workLegend);
  const showSliceLabel = !workLegend && list.length <= 8;
  const legendFormatter = (name) => {
    const item = list.find((i) => i.name === name);
    return item ? `${name}  ${item.value}` : name;
  };
  chart.setOption({
    ...baseChartOptions(),
    tooltip: {
      trigger: "item",
      formatter: (p) => {
        if (!p?.name) return "";
        const pct = p.percent != null ? Number(p.percent).toFixed(1) : "";
        return `${p.name}<br/>数量：${p.value}（${pct}%）`;
      },
    },
    legend: workLegend
      ? {
          show: true,
          type: "scroll",
          orient: "horizontal",
          bottom: 0,
          left: "center",
          width: "92%",
          itemWidth: 10,
          itemHeight: 10,
          itemGap: 8,
          textStyle: { color: C.textDim, fontSize: 9 },
          pageTextStyle: { color: C.textDim },
          formatter: legendFormatter,
        }
      : undefined,
    series: [
      {
        type: "pie",
        radius: workLegend ? ["26%", "44%"] : ["32%", "50%"],
        /* 外侧标签易使整图视觉偏左，略右移圆心以在卡片内水平居中 */
        center: workLegend ? ["53%", "46%"] : ["53%", "54%"],
        data: list,
        label: {
          color: C.text,
          fontSize: 9,
          show: showSliceLabel,
          formatter: "{b}\n{c}",
        },
        labelLine: { show: showSliceLabel, length: 8, length2: 6 },
        itemStyle: {
          borderRadius: 4,
          borderColor: "#061a3a",
          borderWidth: 2,
        },
        color: [C.primary, C.secondary, C.accent, "#5b8ff9", "#61d5a8", "#f6bd16", "#7262fd", "#78d3f8"],
      },
    ],
  });
  return chart;
}

function initSalaryBar() {
  if (!refSalary.value || !payload.value?.salary_buckets) return;
  chartSalary?.dispose();
  chartSalary = echarts.init(refSalary.value, null, { renderer: "canvas" });
  const d = payload.value.salary_buckets;
  chartSalary.setOption({
    ...baseChartOptions(),
    grid: { left: 8, right: 12, bottom: 28, top: 32, containLabel: true },
    xAxis: {
      type: "category",
      data: d.map((x) => x.name),
      axisLabel: { color: C.textDim },
      axisLine: { lineStyle: { color: C.axis } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: C.textDim },
      splitLine: { lineStyle: { color: C.split } },
    },
    series: [{ type: "bar", data: d.map((x) => x.value), itemStyle: { color: C.accent } }],
  });
}

function initKind() {
  if (!refKind.value) return;
  chartKind?.dispose();
  chartKind = echarts.init(refKind.value, null, { renderer: "canvas" });
  const raw = payload.value?.by_job_kind || [];
  const d = [...raw].sort((a, b) => b.value - a.value);
  if (!d.length) {
    chartKind.setOption({
      ...baseChartOptions(),
      title: {
        text: "暂无岗位类型数据",
        left: "center",
        top: "center",
        textStyle: { color: C.textDim, fontSize: 13 },
      },
    });
    return;
  }
  const labels = d.map((x) => `类型 ${String(x.name)}`);
  chartKind.setOption({
    ...baseChartOptions(),
    grid: { left: 4, right: 44, top: 8, bottom: 8, containLabel: true },
    xAxis: {
      type: "value",
      axisLabel: { color: C.textDim, fontSize: 10 },
      splitLine: { lineStyle: { color: C.split } },
    },
    yAxis: {
      type: "category",
      data: labels,
      inverse: true,
      axisLabel: { color: C.text, fontSize: 11 },
      axisLine: { lineStyle: { color: C.axis } },
    },
    series: [
      {
        type: "bar",
        data: d.map((x) => x.value),
        barMaxWidth: 22,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: "#5b8ff9" },
            { offset: 1, color: C.primary },
          ]),
        },
        label: {
          show: true,
          position: "right",
          color: C.accent,
          fontSize: 10,
        },
      },
    ],
  });
}

function resizeAll() {
  [
    chartMap,
    chartLine,
    chartIndustry,
    chartWord,
    chartEdu,
    chartWork,
    chartSalary,
    chartKind,
  ].forEach((c) => c?.resize());
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
    const hasMap = await tryRegisterChinaMap();
    initMap(hasMap);
    initLine();
    initIndustry();
    initHotTagsBar();
    chartEdu?.dispose();
    chartWork?.dispose();
    chartEdu = initDonut(refEdu.value, payload.value.by_education || []);
    chartWork = initDonut(refWork.value, payload.value.by_work_years || [], { workLegend: true });
    initSalaryBar();
    initKind();
    resizeAll();
  } catch (e) {
    loadError.value = e?.message || String(e);
  }
}

function disposeAll() {
  [
    chartMap,
    chartLine,
    chartIndustry,
    chartWord,
    chartEdu,
    chartWork,
    chartSalary,
    chartKind,
  ].forEach((c) => c?.dispose());
  chartMap =
    chartLine =
    chartIndustry =
    chartWord =
    chartEdu =
    chartWork =
    chartSalary =
    chartKind =
      null;
}

onMounted(() => {
  tickClock();
  clockTimer = setInterval(tickClock, 1000);
  load();
  window.addEventListener("resize", resizeAll);
});

onBeforeUnmount(() => {
  clearInterval(clockTimer);
  window.removeEventListener("resize", resizeAll);
  disposeAll();
});
</script>

<style scoped>
.bigscreen {
  --bg-main: #061a3a;
  --bg-panel: #0b2a4a;
  --border: rgba(0, 240, 255, 0.3);
  --primary: #00f0ff;
  --text: #ffffff;
  --text-dim: rgba(255, 255, 255, 0.65);

  min-height: 100vh;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-main);
  color: var(--text);
  font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
  overflow: hidden;
  box-sizing: border-box;
}

.bs-header {
  flex: 0 0 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(0, 240, 255, 0.12), transparent);
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.08);
}

.bs-title {
  margin: 0;
  font-size: 22px;
  font-weight: bold;
  color: var(--primary);
  text-shadow: 0 0 12px rgba(0, 240, 255, 0.45);
}

.bs-sub {
  display: block;
  font-size: 12px;
  color: var(--text-dim);
  margin-top: 2px;
}

.bs-header__nav {
  display: flex;
  gap: 24px;
}

.nav-item {
  font-size: 14px;
  color: var(--text-dim);
  cursor: default;
}

.bs-nav-link {
  margin: 0;
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  font-size: 14px;
  color: var(--primary);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.bs-nav-link:hover {
  color: #fff;
  text-shadow: 0 0 8px rgba(0, 240, 255, 0.5);
}

.bs-header__right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.bs-user-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.bs-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.bs-avatar--placeholder {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 240, 255, 0.12);
  border: 1px dashed rgba(0, 240, 255, 0.35);
  color: var(--primary);
  font-size: 12px;
  font-weight: 700;
}

.bs-user {
  font-size: 14px;
  color: var(--text-dim);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.clock {
  font-size: 15px;
  color: var(--primary);
  font-variant-numeric: tabular-nums;
}

.bs-btn {
  background: rgba(0, 240, 255, 0.12);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 6px 14px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.25s ease;
}

.bs-btn:hover {
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.35);
}

.bs-btn--primary {
  border-color: var(--primary);
  color: var(--primary);
}

.bs-error {
  padding: 24px;
  color: #ff4d4f;
  text-align: center;
}

.bs-scroll {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.bs-main {
  flex: 0 0 auto;
  display: flex;
  gap: 12px;
  padding: 12px;
  align-items: flex-start;
}

.bs-col {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.bs-col--left,
.bs-col--right {
  flex: 0 0 22%;
  max-width: 320px;
}

/* 与中间列取齐高，行业图所在面板可纵向伸展，避免绘图区只占容器一小截 */
.bs-col--right {
  align-self: stretch;
}

.bs-col--center {
  flex: 1;
  min-width: 0;
}

.panel {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px;
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.1);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.panel--grow {
  flex: 0 0 auto;
  min-height: 280px;
}

.panel--industry {
  flex: 1 1 0;
  min-height: 240px;
}

.panel--map {
  flex: 0 0 auto;
  min-height: 320px;
}

.panel__title {
  flex: 0 0 auto;
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(0, 240, 255, 0.2);
}

.panel__title-hint {
  font-size: 11px;
  font-weight: normal;
  color: var(--text-dim);
}

.panel__title-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--primary);
}

.panel__chart {
  flex: 1;
  min-height: 160px;
  min-width: 0;
  overflow: hidden;
  position: relative;
}

.panel__chart--table {
  overflow: auto;
}

.panel__chart--map {
  min-height: 280px;
}

.panel__chart--line {
  min-height: 160px;
}

.panel__chart--footer {
  min-height: 180px;
}

.panel__chart--work-years {
  min-height: 220px;
}

.panel__chart--industry {
  flex: 1 1 0;
  min-height: 200px;
}

.kpi-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.kpi-card {
  flex: 1;
  min-width: 100px;
  background: rgba(0, 240, 255, 0.08);
  border: 1px solid rgba(0, 240, 255, 0.35);
  border-radius: 6px;
  padding: 10px 12px;
  text-align: center;
}

.kpi-card__label {
  font-size: 11px;
  color: var(--text-dim);
}

.kpi-card__value {
  font-size: 22px;
  font-weight: bold;
  color: var(--primary);
  margin-top: 4px;
  text-shadow: 0 0 8px rgba(0, 240, 255, 0.35);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th,
.data-table td {
  padding: 6px 8px;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.data-table th {
  color: var(--primary);
  font-weight: 600;
}

.data-table .num {
  color: #00ffa6;
  font-variant-numeric: tabular-nums;
}

.empty-hint {
  color: var(--text-dim);
  font-size: 13px;
  padding: 12px;
}

.panel__chart--top-salary {
  overflow: auto;
  padding: 2px 0;
}

.top-salary-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.top-salary-row {
  display: flex;
  align-items: stretch;
  gap: 8px;
  padding: 8px 2px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.top-salary-row:last-child {
  border-bottom: none;
}

/* 配图：接口 company_logo；无图时保留虚线占位 */
.top-salary-thumb {
  flex: 0 0 44px;
  width: 44px;
  height: 44px;
  border-radius: 6px;
  background: rgba(0, 240, 255, 0.1);
  border: 1px dashed rgba(0, 240, 255, 0.35);
  align-self: center;
}

.top-salary-thumb--img {
  display: block;
  object-fit: cover;
  border-style: solid;
  border-color: rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.2);
}

.top-salary-body {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.top-salary-rank {
  flex: 0 0 18px;
  font-size: 13px;
  font-weight: bold;
  color: var(--primary);
}

.top-salary-info {
  flex: 1;
  min-width: 0;
}

.top-salary-title {
  font-size: 12px;
  color: var(--text);
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.top-salary-meta {
  font-size: 11px;
  color: var(--text-dim);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top-salary-money {
  flex: 0 0 auto;
  font-size: 12px;
  font-weight: 600;
  color: #ffd54f;
  text-align: right;
  max-width: 100px;
}

.bs-footer {
  flex: 0 0 auto;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 0 12px 20px;
  min-height: 0;
}

.panel--footer {
  min-height: 0;
}

@media (max-width: 1200px) {
  .bs-main {
    flex-direction: column;
  }
  .bs-col--left,
  .bs-col--right {
    flex: none;
    max-width: none;
    width: 100%;
  }
  .bs-footer {
    grid-template-columns: repeat(2, 1fr);
  }

}
</style>

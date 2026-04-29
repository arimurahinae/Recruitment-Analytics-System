<template>
  <div class="job-detail-page">
    <div class="jd-head">
      <div class="jd-head-left">
        <h1 class="jd-title">岗位详情</h1>
        <p class="jd-sub">ID：{{ item.job_jobId || "-" }} · 来自系统岗位数据</p>
      </div>
      <div class="jd-head-actions">
        <el-button type="primary" plain @click="goBack">返回列表</el-button>
        <el-link v-if="item.job_link" :href="item.job_link" target="_blank" type="primary" class="jd-link-btn">猎聘原文</el-link>
      </div>
    </div>

    <el-card shadow="never" class="jd-hero-card" v-loading="loading">
      <div class="jd-job-head">
        <div class="jd-job-main">
          <h2 class="jd-job-title">{{ item.job_title || "-" }}</h2>
          <div class="jd-job-meta">{{ item.company_name || "-" }} · {{ item.query_city_name || "-" }} · {{ item.job_jobKind || "-" }}</div>
        </div>
        <div class="jd-job-salary">{{ item.job_salary || formatSalary(item) }}</div>
      </div>
    </el-card>

    <el-row :gutter="14" class="jd-stat-row">
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="never" class="jd-stat-card">
          <div class="stat-label">岗位城市</div>
          <div class="stat-value">{{ item.query_city_name || "-" }}</div>
          <div class="stat-sub">主查询城市</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="never" class="jd-stat-card">
          <div class="stat-label">学历要求</div>
          <div class="stat-value">{{ item.job_requireEduLevel || "-" }}</div>
          <div class="stat-sub">岗位学历要求</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="never" class="jd-stat-card">
          <div class="stat-label">工作年限</div>
          <div class="stat-value">{{ item.job_requireWorkYears || "-" }}</div>
          <div class="stat-sub">岗位经验要求</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="never" class="jd-stat-card">
          <div class="stat-label">最近刷新</div>
          <div class="stat-value stat-value--time">{{ item.job_refreshTime || "-" }}</div>
          <div class="stat-sub">数据刷新时间</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="14">
      <el-col :xs="24" :lg="15">
        <el-card shadow="never" class="sub-card">
          <template #header>岗位关键信息</template>
          <el-row :gutter="10">
            <el-col :xs="24" :sm="12"><div class="kv"><span>工作城市</span><b>{{ item.query_city_name || "-" }}</b></div></el-col>
            <el-col :xs="24" :sm="12"><div class="kv"><span>岗位类型</span><b>{{ item.job_jobKind || "-" }}</b></div></el-col>
            <el-col :xs="24" :sm="12"><div class="kv"><span>学历要求</span><b>{{ item.job_requireEduLevel || "-" }}</b></div></el-col>
            <el-col :xs="24" :sm="12"><div class="kv"><span>工作年限</span><b>{{ item.job_requireWorkYears || "-" }}</b></div></el-col>
            <el-col :xs="24" :sm="12"><div class="kv"><span>刷新时间</span><b>{{ item.job_refreshTime || "-" }}</b></div></el-col>
            <el-col :xs="24" :sm="12"><div class="kv"><span>创建/更新</span><b>{{ item.updated_at || "-" }}</b></div></el-col>
            <el-col :xs="24"><div class="kv"><span>外部ID</span><b>{{ item.job_jobId || "-" }}</b></div></el-col>
            <el-col :xs="24"><div class="kv"><span>岗位链接</span><b class="text-cut">{{ item.job_link || "-" }}</b></div></el-col>
          </el-row>
        </el-card>

        <el-card shadow="never" class="sub-card mt14">
          <template #header>岗位标签</template>
          <div class="tags">
            <el-tag v-for="(t, i) in parsedTags" :key="i" size="small" effect="plain">{{ t }}</el-tag>
            <span v-if="!parsedTags.length" class="muted">暂无标签</span>
          </div>
        </el-card>

        <el-card shadow="never" class="sub-card mt14">
          <template #header>岗位描述</template>
          <div class="desc">{{ item.job_j || "暂无岗位描述" }}</div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="9">
        <el-card shadow="never" class="sub-card">
          <template #header>企业信息</template>
          <div class="co-head">
            <img :src="logoUrl(item)" class="co-logo" alt="logo" />
            <div>
              <div class="co-name">{{ item.company_name || "-" }}</div>
              <div class="co-meta">{{ item.company_industry || "-" }}</div>
            </div>
          </div>
          <div class="kv"><span>公司规模</span><b>{{ item.company_scale || "-" }}</b></div>
          <div class="kv"><span>融资阶段</span><b>{{ item.company_stage || "-" }}</b></div>
          <div class="kv"><span>公司主页</span><el-link :href="item.company_link || '#'" type="primary" :underline="false" target="_blank">查看</el-link></div>
        </el-card>

        <el-card shadow="never" class="sub-card mt14">
          <template #header>顾问信息</template>
          <div class="kv"><span>姓名</span><b>{{ item.recruiter_name || "-" }}</b></div>
          <div class="kv"><span>职位</span><b>{{ item.recruiter_title || "-" }}</b></div>
          <div class="kv"><span>活跃天数</span><b>{{ item.recruiter_in_day ?? "-" }}</b></div>
        </el-card>

        <el-card shadow="never" class="sub-card">
          <template #header>薪资解析</template>
          <el-row :gutter="10">
            <el-col :xs="12"><div class="kv"><span>薪资文本</span><b>{{ item.job_salary || "-" }}</b></div></el-col>
            <el-col :xs="12"><div class="kv"><span>薪资区间</span><b>{{ formatSalary(item) }}</b></div></el-col>
            <el-col :xs="12"><div class="kv"><span>最低薪资</span><b>{{ item.salary_min ?? "-" }}</b></div></el-col>
            <el-col :xs="12"><div class="kv"><span>最高薪资</span><b>{{ item.salary_max ?? "-" }}</b></div></el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { fetchJobDetail } from "@/api/job";

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const item = reactive({});

const LIEPIN_LOGO_BASE = "https://image0.lietou-static.com/bg_white_222x222/";

function logoUrl(row) {
  const raw = (row?.company_logo || "").trim();
  if (!raw) return `${LIEPIN_LOGO_BASE}5bfe90cf74719d35745ab55f03a.png`;
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
  if (!name) return `${LIEPIN_LOGO_BASE}5bfe90cf74719d35745ab55f03a.png`;
  const file = /\.(png|jpe?g|gif|webp)$/i.test(name) ? name : `${name}.png`;
  return LIEPIN_LOGO_BASE + file;
}

function formatSalary(row) {
  const a = row?.salary_min;
  const b = row?.salary_max;
  if (a != null && b != null) return `${a}-${b}K`;
  if (b != null) return `最高 ${b}K`;
  if (a != null) return `${a}K起`;
  return "-";
}

const parsedTags = computed(() => {
  const raw = String(item.job_labels || "");
  if (!raw.trim()) return [];
  return raw
    .split(/[、,，;\s]+/)
    .map((x) => x.trim())
    .filter(Boolean)
    .slice(0, 20);
});

async function load() {
  const jobId = route.params.jobId;
  if (!jobId) return;
  loading.value = true;
  try {
    const res = await fetchJobDetail(jobId);
    Object.assign(item, res?.item || {});
  } finally {
    loading.value = false;
  }
}

function goBack() {
  router.push("/workspace/jobs");
}

onMounted(load);
</script>

<style scoped>
.job-detail-page {
  max-width: 1460px;
  margin: 0 auto;
  font-family: "Nunito", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
}
.jd-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; gap: 12px; }
.jd-head-left { min-width: 0; }
.jd-head-actions { display: flex; gap: 10px; align-items: center; }
.jd-title { margin: 0 0 4px; font-size: 21px; font-weight: 700; color: #1a4a6e; }
.jd-sub { margin: 0; font-size: 13px; color: #5a7a94; }
.jd-link-btn { padding: 0 10px; height: 32px; line-height: 32px; border-radius: 6px; border: 1px solid #a8d8ff; background: #edf7ff; }
.jd-hero-card,
.sub-card,
.jd-stat-card { border-radius: 10px; border: 1px solid #b3d9f2; background: #fff; }
.jd-hero-card { margin-bottom: 12px; }
.jd-stat-row { margin-bottom: 14px; }
.jd-job-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.jd-job-main { min-width: 0; }
.jd-job-title { margin: 0; font-size: 28px; color: #1a4a6e; line-height: 1.25; }
.jd-job-meta { margin-top: 6px; color: #6a86a1; font-size: 14px; }
.jd-job-salary { font-size: 26px; font-weight: 700; color: #ec4c64; white-space: nowrap; }
.jd-stat-card { padding: 2px 4px; }
.stat-label { font-size: 12px; color: #7a95ac; }
.stat-value { margin-top: 8px; color: #1c4672; font-size: 28px; font-weight: 700; line-height: 1.2; }
.stat-value--time { font-size: 17px; letter-spacing: 0.2px; }
.stat-sub { margin-top: 6px; font-size: 12px; color: #95aabd; }
.co-head { display: flex; gap: 10px; align-items: center; margin-bottom: 10px; }
.co-logo { width: 52px; height: 52px; border-radius: 10px; object-fit: cover; border: 1px solid rgba(0, 0, 0, 0.07); }
.co-name { font-weight: 700; color: #1a4a6e; font-size: 15px; }
.co-meta { font-size: 12px; color: #6a86a1; margin-top: 3px; }
.kv { display: flex; justify-content: space-between; gap: 10px; padding: 7px 0; border-bottom: 1px dashed rgba(43, 140, 203, 0.14); }
.kv:last-child { border-bottom: none; }
.kv span { color: #6a86a1; font-size: 13px; white-space: nowrap; }
.kv b { color: #1a4a6e; font-weight: 600; text-align: right; word-break: break-all; }
.text-cut { display: inline-block; max-width: 340px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tags { display: flex; gap: 8px; flex-wrap: wrap; }
.muted { color: #9ab0c2; font-size: 12px; }
.mt14 { margin-top: 14px; }
.desc { white-space: pre-wrap; line-height: 1.7; color: #264766; font-size: 14px; min-height: 180px; }

@media (max-width: 992px) {
  .jd-head { flex-wrap: wrap; align-items: flex-start; }
  .jd-job-head { flex-direction: column; align-items: flex-start; }
  .jd-job-salary { font-size: 21px; }
  .jd-job-title { font-size: 22px; }
  .stat-value { font-size: 22px; }
  .stat-value--time { font-size: 15px; }
  .text-cut { max-width: 180px; }
}
</style>

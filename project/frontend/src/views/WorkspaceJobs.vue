<template>
  <div class="jobs-page">
    <div class="jobs-header">
      <h1 class="jobs-title">岗位表格</h1>
      <p class="jobs-sub">支持关键词搜索、高级筛选、分页和猎聘详情跳转。</p>
    </div>

    <el-card shadow="never" class="jobs-filter-card">
      <el-form label-position="top" class="jobs-form">
        <el-row :gutter="12">
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="关键词">
              <el-input v-model="form.keyword" placeholder="岗位名/公司名" clearable @keyup.enter="onSearch" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="城市">
              <el-input v-model="form.city" placeholder="如：广州" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-collapse>
          <el-collapse-item title="高级筛选" name="adv">
            <el-row :gutter="12">
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="行业结构">
                  <el-input v-model="form.industry" placeholder="如：互联网/电商" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="学历要求">
                  <el-input v-model="form.edu" placeholder="如：本科" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="工作年限">
                  <el-input v-model="form.work_years" placeholder="如：3-5年" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="公司规模">
                  <el-input v-model="form.company_scale" placeholder="如：100-499人" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="最低薪资(K)">
                  <el-input-number v-model="form.min_salary" :min="0" :step="1" controls-position="right" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="最高薪资(K)">
                  <el-input-number v-model="form.max_salary" :min="0" :step="1" controls-position="right" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="每页条数">
                  <el-select v-model="pager.page_size" style="width: 100%">
                    <el-option :value="10" label="10" />
                    <el-option :value="20" label="20" />
                    <el-option :value="50" label="50" />
                    <el-option :value="100" label="100" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
        </el-collapse>

        <div class="jobs-actions">
          <el-button type="primary" :loading="loading" @click="onSearch">搜索</el-button>
          <el-button @click="onReset">重置</el-button>
        </div>
      </el-form>
    </el-card>

    <el-card shadow="never" class="jobs-table-card">
      <el-table :data="rows" border stripe size="small" v-loading="loading" empty-text="暂无数据">
        <el-table-column label="图片" width="88">
          <template #default="{ row }">
            <a :href="row.job_link || '#'" target="_blank" rel="noopener noreferrer">
              <img :src="logoUrl(row)" class="job-logo" alt="logo" />
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="job_title" label="岗位" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" :underline="false" @click="goDetail(row)">
              {{ row.job_title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="company_name" label="公司" min-width="130" show-overflow-tooltip />
        <el-table-column prop="query_city_name" label="城市" width="90" />
        <el-table-column prop="job_requireEduLevel" label="学历" width="90" />
        <el-table-column prop="job_requireWorkYears" label="经验" width="110" />
        <el-table-column prop="job_salary" label="薪资" width="110" />
        <el-table-column label="猎聘详情" width="100" fixed="right">
          <template #default="{ row }">
            <el-link :href="row.job_link || '#'" type="primary" target="_blank" :underline="false">查看</el-link>
          </template>
        </el-table-column>
      </el-table>

      <div class="jobs-pagination">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next, jumper"
          :total="pager.total"
          :current-page="pager.page"
          :page-size="pager.page_size"
          :page-sizes="[10, 20, 50, 100]"
          @size-change="onSizeChange"
          @current-change="onPageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { fetchJobList } from "@/api/job";
import { useRouter } from "vue-router";

const LIEPIN_LOGO_BASE = "https://image0.lietou-static.com/bg_white_222x222/";
const router = useRouter();

const form = reactive({
  keyword: "",
  city: "",
  industry: "",
  edu: "",
  work_years: "",
  company_scale: "",
  min_salary: 0,
  max_salary: 0,
});

const pager = reactive({
  page: 1,
  page_size: 10,
  total: 0,
});

const loading = ref(false);
const rows = ref([]);

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

async function load() {
  loading.value = true;
  try {
    const res = await fetchJobList({
      ...form,
      page: pager.page,
      page_size: pager.page_size,
    });
    rows.value = res?.items || [];
    pager.total = Number(res?.total || 0);
  } finally {
    loading.value = false;
  }
}

function onSearch() {
  pager.page = 1;
  load();
}

function onReset() {
  form.keyword = "";
  form.city = "";
  form.industry = "";
  form.edu = "";
  form.work_years = "";
  form.company_scale = "";
  form.min_salary = 0;
  form.max_salary = 0;
  pager.page = 1;
  pager.page_size = 10;
  load();
}

function onPageChange(page) {
  pager.page = page;
  load();
}

function onSizeChange(size) {
  pager.page_size = size;
  pager.page = 1;
  load();
}

onMounted(() => {
  load();
});

function goDetail(row) {
  if (!row?.job_jobId) return;
  router.push(`/workspace/jobs/${row.job_jobId}`);
}
</script>

<style scoped>
.jobs-page {
  max-width: 1460px;
  margin: 0 auto;
}

.jobs-header {
  margin-bottom: 12px;
}

.jobs-title {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 700;
  color: #1a4a6e;
}

.jobs-sub {
  margin: 0;
  font-size: 13px;
  color: #5a7a94;
}

.jobs-filter-card,
.jobs-table-card {
  border-radius: 10px;
  border: 1px solid #b3d9f2;
  background: #fff;
  margin-bottom: 12px;
}

.jobs-actions {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}

.job-logo {
  width: 42px;
  height: 42px;
  border-radius: 6px;
  object-fit: cover;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.jobs-pagination {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>

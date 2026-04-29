<template>
  <div class="sp-page">
    <div class="sp-header">
      <h1 class="sp-title">薪资预测</h1>
      <p class="sp-sub">基于 TensorFlow 文本嵌入 + 数值特征的多输入融合模型（此页面先做特征录入与结果展示占位）。</p>
    </div>

    <el-card shadow="never" class="sp-card">
      <template #header>
        <div class="sp-card-hd">
          <span>业务场景 · 特征输入</span>
          <span class="sp-card-hd-sub">你后续可把这些字段直接传给后端预测函数。</span>
        </div>
      </template>

      <el-form label-position="top" class="sp-form">
        <el-row :gutter="12">
          <el-col :xs="24" :sm="12" :lg="8">
            <el-form-item label="岗位名称">
              <el-input v-model="form.job_title" placeholder="如：数据分析师" clearable />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="8">
            <el-form-item label="公司名称">
              <el-input v-model="form.company" placeholder="如：某互联网公司" clearable />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="8">
            <el-form-item label="行业结构">
              <el-input v-model="form.industry" placeholder="如：互联网/电商" clearable />
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :lg="8">
            <el-form-item label="城市">
              <el-input v-model="form.city" placeholder="如：广州" clearable />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="8">
            <el-form-item label="工作年限">
              <el-select v-model="form.work_years" placeholder="选择" clearable style="width: 100%">
                <el-option label="不限" value="" />
                <el-option label="应届" value="应届" />
                <el-option label="1-3年" value="1-3年" />
                <el-option label="3-5年" value="3-5年" />
                <el-option label="5-10年" value="5-10年" />
                <el-option label="10年以上" value="10年以上" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="8">
            <el-form-item label="学历要求">
              <el-select v-model="form.edu" placeholder="选择" clearable style="width: 100%">
                <el-option label="不限" value="" />
                <el-option label="大专" value="大专" />
                <el-option label="本科" value="本科" />
                <el-option label="硕士" value="硕士" />
                <el-option label="博士" value="博士" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24">
            <el-form-item label="岗位描述">
              <el-input v-model="form.job_desc" type="textarea" :rows="4" placeholder="粘贴岗位描述文本，用于 Text Embedding" />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="sp-actions">
          <el-button type="primary" @click="onPredict">本地占位预测</el-button>
          <el-button @click="onReset">重置</el-button>
        </div>
      </el-form>
    </el-card>

    <el-row :gutter="12">
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="sp-card">
          <template #header>输出 · 预测结果（占位）</template>
          <div class="sp-result">
            <div class="sp-kv"><span>预测最低薪资(K)</span><b>{{ result.min_k }}</b></div>
            <div class="sp-kv"><span>预测最高薪资(K)</span><b>{{ result.max_k }}</b></div>
            <p class="sp-note">说明：当前按钮仅生成占位结果。你接入后端时，把表单字段作为特征传给 `model/salary_predictor_tf.py` 的 `predict()` 即可。</p>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="sp-card">
          <template #header>调试 · 特征 JSON</template>
          <pre class="sp-pre">{{ pretty }}</pre>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, reactive } from "vue";

const form = reactive({
  job_title: "",
  job_desc: "",
  company: "",
  industry: "",
  city: "",
  work_years: "",
  edu: "",
});

const result = reactive({
  min_k: "-",
  max_k: "-",
});

const pretty = computed(() => JSON.stringify(form, null, 2));

function onReset() {
  form.job_title = "";
  form.job_desc = "";
  form.company = "";
  form.industry = "";
  form.city = "";
  form.work_years = "";
  form.edu = "";
  result.min_k = "-";
  result.max_k = "-";
}

function onPredict() {
  // 占位逻辑：用输入长度生成一个稳定的伪结果，便于你先把页面跑通
  const seed =
    (form.job_title.length + form.company.length + form.city.length) * 7 +
    (form.job_desc.length % 97) +
    (form.industry.length % 53);
  const min = Math.max(3, Math.round((seed % 40) + 8));
  const max = Math.max(min + 2, Math.round(min + 6 + (seed % 25)));
  result.min_k = String(min);
  result.max_k = String(max);
}
</script>

<style scoped>
.sp-page { max-width: 1460px; margin: 0 auto; }
.sp-header { margin-bottom: 12px; }
.sp-title { margin: 0 0 6px; font-size: 22px; font-weight: 700; color: #1a4a6e; }
.sp-sub { margin: 0; font-size: 13px; color: #5a7a94; }

.sp-card { border-radius: 10px; border: 1px solid #b3d9f2; background: #fff; margin-bottom: 12px; }
.sp-card-hd { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }
.sp-card-hd-sub { font-size: 12px; color: #7a95ac; }

.sp-actions { margin-top: 10px; display: flex; gap: 10px; }

.sp-result { padding: 4px 2px; }
.sp-kv { display: flex; justify-content: space-between; gap: 10px; padding: 10px 0; border-bottom: 1px dashed rgba(43, 140, 203, 0.14); }
.sp-kv:last-child { border-bottom: none; }
.sp-kv span { color: #6a86a1; font-size: 13px; }
.sp-kv b { color: #1a4a6e; font-weight: 700; }
.sp-note { margin: 10px 0 0; font-size: 12px; color: #7a95ac; line-height: 1.6; }

.sp-pre { margin: 0; padding: 10px; background: #f3fbff; border: 1px solid rgba(43, 140, 203, 0.18); border-radius: 8px; color: #244b6b; font-size: 12px; overflow: auto; max-height: 260px; }
</style>


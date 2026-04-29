<template>
  <div class="profile-page">
    <div class="profile-header">
      <div class="profile-header__left">
        <h1 class="profile-title">{{ T.title }}</h1>
        <p class="profile-sub">{{ T.subtitle }}</p>
      </div>
      <div class="profile-header__right">
        <el-button @click="onReset">{{ T.reset }}</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">{{ T.save }}</el-button>
      </div>
    </div>

    <el-row :gutter="14" class="profile-topcards">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="never" class="profile-stat-card">
          <div class="profile-stat-label">{{ T.cardNickname }}</div>
          <div class="profile-stat-value">{{ user.username || T.notSet }}</div>
          <div class="profile-stat-hint">{{ T.cardNicknameHint }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="never" class="profile-stat-card">
          <div class="profile-stat-label">{{ T.cardDeliveryTag }}</div>
          <div class="profile-stat-value">{{ user.delivery_tag || T.notSet }}</div>
          <div class="profile-stat-hint">{{ T.cardDeliveryTagHint }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="never" class="profile-stat-card">
          <div class="profile-stat-label">{{ T.cardNotify }}</div>
          <div class="profile-stat-value">{{ notifyText }}</div>
          <div class="profile-stat-hint">{{ T.cardNotifyHint }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="never" class="profile-stat-card">
          <div class="profile-stat-label">{{ T.cardRemember }}</div>
          <div class="profile-stat-value">{{ user.remember_device ? T.on : T.off }}</div>
          <div class="profile-stat-hint">{{ T.cardRememberHint }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="14" class="profile-grid">
      <el-col :xs="24" :lg="14">
        <div class="profile-col">
        <el-card shadow="never" class="profile-card profile-card--base">
          <template #header>
            <div class="card-title">
              <span>{{ T.blockBase }}</span>
              <span class="card-title__hint">{{ T.blockBaseHint }}</span>
            </div>
          </template>
          <el-row :gutter="18">
            <el-col :xs="24" :sm="8">
              <div class="avatar-block">
                <el-avatar :size="96" :src="form.avatar || defaultAvatar">
                  <span v-if="!form.avatar">{{ initials }}</span>
                </el-avatar>
                <div class="avatar-btns">
                  <el-upload
                    class="avatar-uploader"
                    :show-file-list="false"
                    :before-upload="beforeUpload"
                    :on-change="onAvatarChange"
                  >
                    <el-button size="small" type="primary" plain>{{ T.uploadAvatar }}</el-button>
                  </el-upload>
                  <el-button size="small" @click="form.avatar = ''">{{ T.removeAvatar }}</el-button>
                </div>
                <div class="avatar-tip">{{ T.avatarTip }}</div>
              </div>
            </el-col>
            <el-col :xs="24" :sm="16">
              <el-form :model="form" label-position="top" class="profile-form">
                <el-form-item :label="T.nickname">
                  <el-input v-model="form.username" :placeholder="T.nicknamePh" maxlength="32" show-word-limit />
                </el-form-item>
                <el-row :gutter="12">
                  <el-col :xs="24" :sm="12">
                    <el-form-item :label="T.titleLabel">
                      <el-input v-model="form.title" :placeholder="T.titlePh" maxlength="40" show-word-limit />
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :sm="12">
                    <el-form-item :label="T.teamLabel">
                      <el-input v-model="form.team" :placeholder="T.teamPh" maxlength="40" show-word-limit />
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-row :gutter="12">
                  <el-col :xs="24" :sm="12">
                    <el-form-item :label="T.deliveryTag">
                      <el-input v-model="form.delivery_tag" :placeholder="T.deliveryTagPh" maxlength="20" show-word-limit />
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :sm="12">
                    <el-form-item :label="T.officeLabel">
                      <el-input v-model="form.office" :placeholder="T.officePh" maxlength="40" show-word-limit />
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </el-col>
          </el-row>
        </el-card>
        <el-card shadow="never" class="profile-card profile-card--bio profile-card--bio-left">
          <template #header>
            <div class="card-title">
              <span>{{ T.blockBio }}</span>
              <span class="card-title__hint">{{ T.blockBioHint }}</span>
            </div>
          </template>
          <el-input
            v-model="form.bio"
            type="textarea"
            :rows="7"
            maxlength="300"
            show-word-limit
            :placeholder="T.bioPh"
          />
        </el-card>
        </div>
      </el-col>

      <el-col :xs="24" :lg="10" >
        <div class="profile-col profile-col--right">
        <el-card shadow="never" class="profile-card profile-card--contact">
          <template #header>
            <div class="card-title">
              <span>{{ T.blockContact }}</span>
              <span class="card-title__hint">{{ T.blockContactHint }}</span>
            </div>
          </template>
          <el-form :model="form" label-position="top" class="profile-form">
            <el-form-item :label="T.emailLabel">
              <el-input v-model="form.email" :placeholder="T.emailPh" maxlength="120" show-word-limit />
            </el-form-item>
            <el-form-item :label="T.phoneLabel">
              <el-input v-model="form.phone" :placeholder="T.phonePh" maxlength="20" show-word-limit />
            </el-form-item>
            <el-form-item :label="T.skillsLabel">
              <el-input v-model="form.skills" :placeholder="T.skillsPh" maxlength="80" show-word-limit />
            </el-form-item>

            <div class="split-line" />

            <div class="switch-row">
              <div class="switch-text">
                <div class="switch-title">{{ T.notifyEmailTitle }}</div>
                <div class="switch-sub">{{ T.notifyEmailSub }}</div>
              </div>
              <el-switch v-model="form.notify_email" />
            </div>
            <div class="switch-row">
              <div class="switch-text">
                <div class="switch-title">{{ T.notifySmsTitle }}</div>
                <div class="switch-sub">{{ T.notifySmsSub }}</div>
              </div>
              <el-switch v-model="form.notify_sms" />
            </div>

            <div class="split-line" />

            <div class="switch-row">
              <div class="switch-text">
                <div class="switch-title">{{ T.rememberTitle }}</div>
                <div class="switch-sub">{{ T.rememberSub }}</div>
              </div>
              <el-switch v-model="form.remember_device" />
            </div>
          </el-form>
        </el-card>
        </div>
      </el-col>
    </el-row>

  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useCurrentUser } from "@/composables/useCurrentUser";
import { meApi, updateMeApi } from "@/api/auth";

const { user, setUser, reloadUser } = useCurrentUser();

const saving = ref(false);

// ASCII-only: avoid encoding problems by using \u escapes.
const T = {
  title: "\u4e2a\u4eba\u4fe1\u606f\u7ba1\u7406", 
  subtitle: "\u4fdd\u5b58\u8d44\u6599\u540e\uff0c\u4eea\u8868\u76d8\u4e0e\u5927\u5c4f\u5c06\u7acb\u5373\u66f4\u65b0\u663e\u793a\u5934\u50cf\u4e0e\u7528\u6237\u540d\u3002", 
  reset: "\u91cd\u7f6e", 
  save: "\u4fdd\u5b58\u4fee\u6539", 
  notSet: "\u672a\u8bbe\u7f6e", 
  on: "\u5f00\u542f", 
  off: "\u5173\u95ed", 

  cardNickname: "\u663e\u793a\u6635\u79f0", 
  cardNicknameHint: "\u7528\u4e8e\u4eea\u8868\u76d8\u4e0e\u5927\u5c4f\u5c55\u793a", 
  cardDeliveryTag: "\u6295\u9012\u6807\u7b7e", 
  cardDeliveryTagHint: "\u65b9\u4fbf\u56e2\u961f\u4e86\u89e3\u4f60\u7684\u504f\u597d", 
  cardNotify: "\u901a\u77e5\u65b9\u5f0f", 
  cardNotifyHint: "\u7528\u4e8e\u91cd\u8981\u53d8\u66f4\u63d0\u9192", 
  cardRemember: "\u8bb0\u4f4f\u8bbe\u5907", 
  cardRememberHint: "\u51b3\u5b9a\u662f\u5426\u4fdd\u5b58\u672c\u5730\u4f1a\u8bdd", 

  blockBase: "\u5934\u50cf\u4e0e\u57fa\u7840\u4fe1\u606f", 
  blockBaseHint: "\u540c\u6b65\u81f3\u9996\u9875\u4e0e\u5927\u5c4f", 
  uploadAvatar: "\u4e0a\u4f20\u5934\u50cf", 
  removeAvatar: "\u79fb\u9664\u5934\u50cf", 
  avatarTip: "\u652f\u6301 JPG / PNG\uff0c\u672c\u5730\u4e0a\u4f20\u4f1a\u8f6c\u4e3a DataURL\uff08\u6f14\u793a\u7528\uff09", 

  nickname: "\u663e\u793a\u6635\u79f0", 
  nicknamePh: "\u8bf7\u8f93\u5165\u6635\u79f0", 
  titleLabel: "\u804c\u4f4d/\u5934\u8854", 
  titlePh: "\u5982\uff1a\u62db\u8058\u6570\u636e\u5206\u6790\u5e08", 
  teamLabel: "\u6240\u5c5e\u56e2\u961f", 
  teamPh: "\u5982\uff1a\u62db\u8058\u6570\u636e\u4e2d\u53f0", 
  deliveryTag: "\u6295\u9012\u6807\u7b7e", 
  deliveryTagPh: "\u5982\uff1a\u6821\u62db / \u793e\u62db / \u5b9e\u4e60", 
  officeLabel: "\u529e\u516c\u5730\u70b9", 
  officePh: "\u5982\uff1a\u5e7f\u4e1c \u00b7 \u5e7f\u5dde", 

  blockContact: "\u8054\u7cfb\u65b9\u5f0f", 
  blockContactHint: "\u4ec5\u7528\u4e8e\u7ad9\u5185\u901a\u77e5", 
  emailLabel: "\u90ae\u7bb1", 
  emailPh: "name@example.com", 
  phoneLabel: "\u624b\u673a\u53f7", 
  phonePh: "11 \u4f4d\u624b\u673a\u53f7", 
  skillsLabel: "\u64c5\u957f\u6807\u7b7e", 
  skillsPh: "\u5982\uff1a\u6570\u636e\u5206\u6790 / \u53ef\u89c6\u5316 / Django / Vue", 

  notifyEmailTitle: "\u90ae\u4ef6\u63d0\u9192", 
  notifyEmailSub: "\u91cd\u8981\u6c47\u603b\u4e0e\u5173\u952e\u6570\u636e\u53d8\u5316", 
  notifySmsTitle: "\u77ed\u4fe1\u63d0\u9192", 
  notifySmsSub: "\u5173\u952e\u5f02\u5e38\u6216\u7d27\u6025\u901a\u77e5", 
  rememberTitle: "\u8bb0\u4f4f\u6b64\u8bbe\u5907", 
  rememberSub: "\u51cf\u5c11\u91cd\u590d\u767b\u5f55\uff08\u4ec5\u5f53\u524d\u6d4f\u89c8\u5668\uff09", 

  blockBio: "\u4e2a\u4eba\u7b80\u4ecb", 
  blockBioHint: "\u7528\u4e8e\u5c55\u793a\u5728\u56e2\u961f\u6210\u5458\u5361\u7247", 
  bioPh: "\u7b80\u5355\u4ecb\u7ecd\u4e00\u4e0b\u4f60\u7684\u80cc\u666f\u3001\u64c5\u957f\u65b9\u5411\u548c\u9879\u76ee\u7ecf\u5386", 
};

const form = reactive({
  username: "",
  avatar: "",
  email: "",
  phone: "",
  title: "",
  team: "",
  office: "",
  skills: "",
  delivery_tag: "",
  notify_email: true,
  notify_sms: false,
  remember_device: true,
  bio: "",
});

const defaultAvatar = computed(() => {
  const name = user.username || "\u7528\u6237";
  const code = name.codePointAt(0) || "\u7528".codePointAt(0);
  const hue = code % 360;
  const seed = encodeURIComponent(name);
  return `https://api.dicebear.com/7.x/initials/svg?seed=${seed}&backgroundColor=hsl(${hue},70%,75%)`;
});

const initials = computed(() => (user.username || "\u7528").slice(0, 2).toUpperCase());

const notifyText = computed(() => {
  const parts = [];
  if (user.notify_email) parts.push("\u90ae\u4ef6");
  if (user.notify_sms) parts.push("\u77ed\u4fe1");
  return parts.length ? parts.join(" + ") : "\u5173\u95ed";
});

function syncFromUser() {
  reloadUser();
  form.username = user.username || "";
  form.avatar = user.avatar || "";
  form.email = user.email || "";
  form.phone = user.phone || "";
  form.bio = user.bio || "";
  form.title = user.title || "";
  form.team = user.team || "";
  form.office = user.office || "";
  form.skills = user.skills || "";
  form.delivery_tag = user.delivery_tag || "";
  form.notify_email = user.notify_email !== false;
  form.notify_sms = Boolean(user.notify_sms);
  form.remember_device = user.remember_device !== false;
}

syncFromUser();

// ����ҳ��ʱ�Է����Ϊ׼����֤�´ε�¼�Ա�����
(async () => {
  try {
    const data = await meApi();
    if (data?.ok && data?.user) {
      setUser(data.user);
      syncFromUser();
    }
  } catch {
    // ���ԣ����߻����˲�����ʱ����ʹ�ñ��ػ���
  }
})();

function beforeUpload() {
  return false;
}

function onAvatarChange(file) {
  if (!file.raw) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    const url = e.target?.result;
    if (typeof url === "string") form.avatar = url;
  };
  reader.readAsDataURL(file.raw);
}

async function onSave() {
  if (!form.username.trim()) {
    ElMessage.warning("\u663e\u793a\u6635\u79f0\u4e0d\u80fd\u4e3a\u7a7a");
    return;
  }
  saving.value = true;
  try {
    const payload = {
      username: form.username.trim(),
      avatar: form.avatar.trim(),
      email: form.email.trim(),
      phone: form.phone.trim(),
      bio: form.bio || "",
      title: form.title.trim(),
      team: form.team.trim(),
      office: form.office.trim(),
      skills: form.skills.trim(),
      delivery_tag: form.delivery_tag.trim(),
      notify_email: Boolean(form.notify_email),
      notify_sms: Boolean(form.notify_sms),
      remember_device: Boolean(form.remember_device),
    };

    const res = await updateMeApi(payload);
    if (res?.ok && res?.user) {
      setUser(res.user);
      syncFromUser();
      ElMessage.success(res.message || "\u4fdd\u5b58\u6210\u529f");
    } else {
      ElMessage.error(res?.message || "\u4fdd\u5b58\u5931\u8d25");
    }
  } finally {
    saving.value = false;
  }
}

function onReset() {
  syncFromUser();
}
</script>

<style scoped>
.profile-page {
  max-width: 1180px;
  margin: 0 auto;
}

.profile-header {
  margin-bottom: 16px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.profile-header__right {
  display: flex;
  gap: 10px;
  flex: 0 0 auto;
}

.profile-topcards {
  margin-bottom: 14px;
}

.profile-grid {
  align-items: stretch;
}

.profile-col {
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 100%;
}

.profile-col--right {
  height: 100%;
}

.profile-stat-card {
  border-radius: 10px;
  border: 1px solid #b3d9f2;
  background: linear-gradient(180deg, #ffffff 0%, #f5fbff 100%);
}

.profile-stat-label {
  font-size: 12px;
  color: #5a7a94;
  margin-bottom: 6px;
}

.profile-stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #2b8ccb;
  font-variant-numeric: tabular-nums;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-stat-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #7a94ab;
}

.profile-title {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 700;
  color: #1a4a6e;
}

.profile-sub {
  margin: 0;
  font-size: 13px;
  color: #5a7a94;
}

.profile-card {
  border-radius: 10px;
  border: 1px solid #b3d9f2;
  background: #fff;
  margin-bottom: 14px;
}

.profile-card--base {
  min-height: 320px;
}

.profile-card--contact {
  flex: 1;
  min-height: 520px;
}

.profile-card--bio-left {
  flex: 1;
  min-height: 260px;
}

.card-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  font-weight: 600;
  color: #1a4a6e;
}

.card-title__hint {
  font-weight: 400;
  font-size: 12px;
  color: #7a94ab;
}

.avatar-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding-top: 6px;
}

.avatar-btns {
  display: flex;
  gap: 10px;
}

.avatar-tip {
  font-size: 12px;
  color: #7a94ab;
  text-align: center;
}

.profile-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.split-line {
  height: 1px;
  background: rgba(43, 140, 203, 0.18);
  margin: 10px 0 12px;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 0;
}

.switch-title {
  font-size: 13px;
  font-weight: 600;
  color: #1a4a6e;
}

.switch-sub {
  font-size: 12px;
  color: #7a94ab;
  margin-top: 2px;
}

.profile-card--bio {
  margin-top: 2px;
}
</style>



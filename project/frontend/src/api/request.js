import axios from "axios";
import { ElMessage } from "element-plus";
import router from "@/router";

const request = axios.create({
  baseURL: "/api",
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

request.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

request.interceptors.response.use(
  (res) => {
    const data = res.data;
    if (typeof data === "string" && data.trimStart().startsWith("<")) {
      return Promise.reject(
        new Error(
          "接口返回了网页而非 JSON：请先启动 Django（python manage.py runserver），并确认 dev/preview 已配置 /api 代理到 8000 端口"
        )
      );
    }
    return data;
  },
  (err) => {
    const d = err.response?.data;
    let msg =
      (typeof d === "object" && d?.message) ||
      err.message ||
      "请求失败";
    if (typeof d === "object" && d?.detail) {
      msg = `${msg}（${d.detail}）`;
    }
    if (err.response?.status === 401) {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
      if (router.currentRoute.value.name !== "Login") {
        router.push({ name: "Login" });
      }
    }
    ElMessage.error(typeof msg === "string" ? msg : JSON.stringify(msg));
    return Promise.reject(err);
  }
);

export default request;

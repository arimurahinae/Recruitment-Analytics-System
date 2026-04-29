import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    redirect: "/workspace",
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("@/views/Login.vue"),
    meta: { guest: true },
  },
  {
    path: "/register",
    name: "Register",
    component: () => import("@/views/Register.vue"),
    meta: { guest: true },
  },
  {
    path: "/workspace",
    component: () => import("@/layouts/WorkspaceLayout.vue"),
    meta: { requiresAuth: true },
    children: [
      {
        path: "",
        name: "WorkspaceHome",
        component: () => import("@/views/WorkspaceDashboard.vue"),
      },
      {
        path: "profile",
        name: "WorkspaceProfile",
        component: () => import("@/views/WorkspaceProfile.vue"),
      },
      {
        path: "jobs",
        name: "WorkspaceJobs",
        component: () => import("@/views/WorkspaceJobs.vue"),
      },
      {
        path: "jobs/:jobId",
        name: "WorkspaceJobDetail",
        component: () => import("@/views/WorkspaceJobDetail.vue"),
      },
      {
        path: "salary-predict",
        name: "WorkspaceSalaryPredict",
        component: () => import("@/views/WorkspaceSalaryPredict.vue"),
      },
    ],
  },
  {
    path: "/bigscreen",
    name: "BigScreen",
    component: () => import("@/views/DashboardBigScreen.vue"),
    meta: { requiresAuth: true },
  },
  /** 旧地址兼容：原先大屏挂在 /dashboard */
  {
    path: "/dashboard",
    redirect: "/bigscreen",
  },
  {
    path: "/home",
    name: "Home",
    component: () => import("@/views/Home.vue"),
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

function syncHtmlTheme(to) {
  const light = /^\/workspace(\/|$)/.test(to.path);
  document.documentElement.classList.toggle("dark", !light);
}

router.afterEach((to) => {
  syncHtmlTheme(to);
});

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem("auth_token");
  if (to.meta.requiresAuth && !token) {
    next({ name: "Login", query: { redirect: to.fullPath } });
    return;
  }
  if (to.meta.guest && token && (to.name === "Login" || to.name === "Register")) {
    next({ name: "WorkspaceHome" });
    return;
  }
  next();
});

export default router;

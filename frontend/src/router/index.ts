import { createRouter, createWebHistory } from "vue-router";

import { useAuthStore } from "../stores/auth";
import Dashboard from "../views/Dashboard.vue";
import EmptyModule from "../views/EmptyModule.vue";
import Login from "../views/Login.vue";
import Settings from "../views/Settings.vue";
import Setup from "../views/Setup.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/dashboard" },
    { path: "/login", component: Login, meta: { public: true } },
    { path: "/setup", component: Setup, meta: { public: true } },
    { path: "/dashboard", component: Dashboard },
    { path: "/settings", component: Settings },
    { path: "/scripts", component: EmptyModule, props: { title: "脚本库", eyebrow: "EXECUTION / SCRIPTS" } },
    { path: "/tickets", component: EmptyModule, props: { title: "人工工单", eyebrow: "HUMAN / TICKETS" } },
    { path: "/chat", component: EmptyModule, props: { title: "ChatOps", eyebrow: "AGENT / CHATOPS" } },
  ],
});

router.beforeEach((to) => {
  const auth = useAuthStore();
  if (!to.meta.public && !auth.isAuthenticated) return "/login";
  if (to.path === "/login" && auth.isAuthenticated) return "/dashboard";
  return true;
});

export default router;

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ChatDotRound,
  Collection,
  DataAnalysis,
  HelpFilled,
  List,
  Setting,
} from "@element-plus/icons-vue";

import { useAuthStore } from "../stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const navigation = [
  { path: "/dashboard", label: "总览", caption: "DASHBOARD", icon: DataAnalysis },
  { path: "/chat", label: "ChatOps", caption: "AI CONSOLE", icon: ChatDotRound },
  { path: "/scripts", label: "脚本库", caption: "EXECUTION", icon: Collection },
  { path: "/tickets", label: "人工工单", caption: "HUMAN LOOP", icon: List },
  { path: "/settings", label: "系统设置", caption: "CONTROL PLANE", icon: Setting },
];

const pageTitle = computed(() => navigation.find((item) => item.path === route.path)?.label || "总览");

function go(path: string) {
  router.push(path);
}

function logout() {
  auth.logout();
  router.push("/login");
}
</script>

<template>
  <div class="app-shell">
    <aside class="side-nav">
      <div class="brand-lockup">
        <div class="brand-mark"><span></span><span></span><span></span></div>
        <div>
          <strong>AutoHeal</strong>
          <small>OPS INTELLIGENCE</small>
        </div>
      </div>

      <div class="nav-section-label">CONTROL ROOM</div>
      <nav>
        <button
          v-for="item in navigation"
          :key="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
          type="button"
          @click="go(item.path)"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span><b>{{ item.label }}</b><small>{{ item.caption }}</small></span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <div class="runtime-chip"><span class="status-dot"></span><span>Runtime online</span></div>
        <button class="help-link" type="button"><el-icon><HelpFilled /></el-icon> 文档与帮助</button>
      </div>
    </aside>

    <main class="main-stage">
      <header class="top-bar">
        <div>
          <div class="breadcrumb">AUTOMATED RELIABILITY / {{ pageTitle.toUpperCase() }}</div>
          <h1>{{ pageTitle }}</h1>
        </div>
        <div class="top-actions">
          <div class="operator"><span class="avatar">{{ auth.currentUser?.username?.slice(0, 1).toUpperCase() || "A" }}</span><span>{{ auth.currentUser?.username || "operator" }}</span></div>
          <button class="logout-button" type="button" @click="logout">退出</button>
        </div>
      </header>
      <section class="page-content"><slot /></section>
    </main>
  </div>
</template>

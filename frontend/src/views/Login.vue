<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();
const submitting = ref(false);
const form = reactive({ username: "", password: "" });

async function submit() {
  if (!form.username.trim() || !form.password) {
    ElMessage.warning("请输入用户名和密码");
    return;
  }
  submitting.value = true;
  try {
    await auth.login(form);
    router.push("/dashboard");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "登录失败");
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <main class="auth-page">
    <div class="auth-grid-lines"></div>
    <section class="auth-panel">
      <div class="brand-lockup auth-brand"><div class="brand-mark"><span></span><span></span><span></span></div><div><strong>AutoHeal</strong><small>OPS INTELLIGENCE</small></div></div>
      <div class="auth-copy"><span class="eyebrow">SECURE CONTROL PLANE</span><h1>恢复系统的<br /><em>下一步。</em></h1><p>让告警有迹可循，让每一次修复都能被验证。</p></div>
      <el-form class="auth-form" @submit.prevent="submit">
        <el-form-item label="操作员账号"><el-input v-model="form.username" size="large" autocomplete="username" placeholder="输入管理员账号" /></el-form-item>
        <el-form-item label="访问密码"><el-input v-model="form.password" size="large" type="password" show-password autocomplete="current-password" placeholder="输入密码" @keyup.enter="submit" /></el-form-item>
        <button class="primary-action wide" type="submit" :disabled="submitting"><span>{{ submitting ? "正在验证" : "进入控制台" }}</span><span aria-hidden="true">↗</span></button>
      </el-form>
      <div class="auth-footer"><span class="status-dot"></span>API gateway ready <span class="version">v0.1 / phase 1</span></div>
    </section>
  </main>
</template>

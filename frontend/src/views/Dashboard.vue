<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { getDashboardOverview } from "../api/config";

const loading = ref(true);
const overview = ref<{ setup_completed: boolean; llm_provider: string; llm_api_format: string; llm_model: string; dependencies: Record<string, string> } | null>(null);

async function load() {
  try { overview.value = await getDashboardOverview(); } catch (error) { ElMessage.error(error instanceof Error ? error.message : "概览读取失败"); } finally { loading.value = false; }
}
onMounted(load);
</script>

<template>
  <div v-loading="loading" class="dashboard-view">
    <div class="dashboard-hero"><div><span class="eyebrow">SYSTEM PULSE / LIVE OVERVIEW</span><h2>今天的系统，<em>安静运行。</em></h2><p>AutoHeal 正在等待下一条需要被理解的信号。</p></div><div class="hero-signal"><span class="signal-ring"></span><div><b>OPERATIONAL</b><small>LAST CHECK · JUST NOW</small></div></div></div>
    <div class="metric-grid"><article class="metric-card primary"><span class="metric-label">ACTIVE LLM</span><strong>{{ overview?.llm_model || "—" }}</strong><small>{{ overview?.llm_provider || "—" }} / {{ overview?.llm_api_format || "—" }}</small></article><article class="metric-card"><span class="metric-label">AUTOMATION RATE</span><strong>—</strong><small>等待告警数据接入</small></article><article class="metric-card"><span class="metric-label">MTTR</span><strong>—</strong><small>阶段 2 开始统计</small></article><article class="metric-card"><span class="metric-label">OPEN TICKETS</span><strong>0</strong><small>当前没有人工接管</small></article></div>
    <div class="dashboard-columns"><section class="panel-block"><div class="panel-heading"><div><span class="eyebrow">DEPENDENCY MAP</span><h3>运行依赖</h3></div><span class="section-state">{{ overview?.setup_completed ? "CONFIGURED" : "SETUP REQUIRED" }}</span></div><div class="dependency-list"><div v-for="(status, name) in overview?.dependencies" :key="name"><span class="dep-name">{{ name }}</span><span class="dep-line"></span><span :class="status === 'ok' || status === 'configured' || status === 'not_required' ? 'ok-text' : 'muted-text'">{{ status.toUpperCase() }}</span></div></div></section><section class="panel-block next-panel"><div class="panel-heading"><div><span class="eyebrow">NEXT SIGNAL</span><h3>接入你的第一条告警</h3></div></div><p>Prometheus Webhook 接入后，AutoHeal 会在这里展示告警流和 AI 决策过程。</p><button class="ghost-action" type="button" @click="$router.push('/settings')">前往告警设置 <span>↗</span></button></section></div>
  </div>
</template>

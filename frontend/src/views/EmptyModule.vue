<script setup lang="ts">
defineProps<{ title: string; eyebrow: string }>();
</script>

<template>
  <div class="empty-module"><span class="eyebrow">{{ eyebrow }}</span><div class="empty-icon"><span></span><span></span><span></span></div><h2>{{ title }}<em> soon.</em></h2><p>这个工作区将在下一阶段接入，基础导航和权限已经准备好。</p></div>
</template>

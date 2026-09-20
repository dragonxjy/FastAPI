<script setup>
import AgentChat from '../components/agent/AgentChat.vue'
import TabBar from '../components/TabBar.vue'

// 路由页面只负责组合页面；请求逻辑在 useArticleAgent.js 中。
</script>

<template>
  <main class="agent-page">
    <van-nav-bar :title="$t('aiChat.title')" fixed />
    <AgentChat />
    <TabBar />
  </main>
</template>

<style scoped>
.agent-page {
  height: 100vh;
  height: 100dvh;
  padding-top: 46px;
  padding-bottom: calc(50px + env(safe-area-inset-bottom));
  background: var(--background-color, #fff);
  color: var(--text-color, #333);
}
</style>

<script setup>
import { nextTick, useTemplateRef, watch } from 'vue'
import { useArticleAgent } from '../../composables/useArticleAgent'
import AgentMessage from './AgentMessage.vue'
import AgentComposer from './AgentComposer.vue'

const { messages, input, busy, error, status, statusLoading, statusError, loggedIn, canSend, checkStatus, send, clearChat } = useArticleAgent()
const conversation = useTemplateRef('conversation')
const examples = [
  { label: '查找文章', text: '查找包含“FastAPI”的文章，列出文章 ID、标题和分类。' },
  { label: '新增文章', text: '先查看现有分类，选择最适合的一类新增文章，标题为《我的第一篇 Agent 学习笔记》，正文介绍 FastAPI 和 LangChain 的作用，作者为学习者。' },
  { label: '修改文章', text: '先查找《我的第一篇 Agent 学习笔记》，如果只有一篇，将它的标题改成《我的 Agent 入门笔记》。' },
  { label: '删除文章', text: '先帮我查找《我的 Agent 入门笔记》，列出 ID 和标题，我确认具体文章后再删除。' },
]

watch([() => messages.value.length, busy, error], async () => {
  await nextTick()
  if (conversation.value) conversation.value.scrollTop = conversation.value.scrollHeight
})
</script>

<template>
  <section class="chat" aria-label="文章助手聊天">
    <div class="toolbar">
      <span class="status" role="status">
        <span class="status-dot" :class="{ ready: status?.configured }"></span>
        {{ statusLoading ? '正在检查配置…' : statusError ? '后端连接失败' : status?.configured ? '模型已配置' : '模型未配置' }}
      </span>
      <button class="text-button" :disabled="busy || !messages.length" @click="clearChat">清空对话</button>
    </div>
    <div ref="conversation" class="conversation" role="log" aria-label="聊天记录" aria-live="polite" :aria-busy="busy">
      <div v-if="!messages.length" class="welcome">
        <span class="eyebrow">你的文章工作台</span>
        <h1 class="heading">用一句话，管理文章。</h1>
        <p class="description">查找、新增、修改、删除，把需求告诉助手。它会调用文章工具，并告诉你实际执行的结果。</p>
        <div class="examples">
          <button v-for="example in examples" :key="example.label" class="example" :disabled="busy" @click="input = example.text">
            <span class="example-label">{{ example.label }}</span><span aria-hidden="true">↗</span>
          </button>
        </div>
        <p class="example-hint">点击示例填入输入框，编辑后再发送。</p>
      </div>
      <div v-if="!loggedIn" class="notice">
        <p>登录后，即可管理这个演示项目中的文章。</p>
        <RouterLink class="notice-link" to="/login?redirect=/aichat">去登录 →</RouterLink>
      </div>
      <div v-if="statusError || (status && !status.configured)" class="notice" role="status">
        <p>{{ statusError || '尚未配置大模型。请在项目根目录 .env 填写 API 密钥与模型配置，重启后端后重试。' }}</p>
        <button class="text-button" :disabled="statusLoading" @click="checkStatus">重新检查连接</button>
      </div>
      <p v-if="!messages.length" class="scope-note">这是学习用的共享文章库，登录用户的修改会直接保存。删除时请明确文章 ID。</p>
      <AgentMessage v-for="message in messages" :key="message.id" :message="message" />
      <p v-if="busy" class="thinking" role="status">正在理解你的需求并执行文章工具，请稍候…</p>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
    </div>
    <AgentComposer v-model="input" :busy="busy" :can-send="canSend" @send="send" />
  </section>
</template>

<style scoped>
.chat { display: flex; flex-direction: column; height: 100%; min-height: 0; }
.toolbar { display: flex; align-items: center; justify-content: space-between; padding: 13px 20px; border-bottom: 1px solid color-mix(in srgb, currentColor 10%, transparent); }
.status { display: flex; align-items: center; gap: 7px; font-size: 12px; opacity: .8; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: #999; }
.status-dot.ready { background: #239763; }
.text-button { border: 0; background: transparent; color: var(--primary-color, #1989fa); font-size: 12px; cursor: pointer; padding: 4px 0; }
.text-button:disabled { opacity: .45; cursor: not-allowed; }
.conversation { flex: 1; min-height: 0; overflow-y: auto; padding: 24px 24px 16px; }
.welcome { padding: 16px 0 20px; }
.eyebrow { font-size: 12px; color: var(--primary-color, #1989fa); }
.heading { margin: 10px 0 14px; font-size: 28px; font-weight: 650; letter-spacing: -.5px; }
.description { max-width: 520px; opacity: .75; font-size: 14px; line-height: 1.9; }
.examples { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 22px; }
.example { display: flex; justify-content: space-between; align-items: center; padding: 16px; background: var(--background-color, #fff); color: inherit; border: 1px solid color-mix(in srgb, currentColor 18%, transparent); border-radius: 8px; cursor: pointer; text-align: left; }
.example:hover { border-color: var(--primary-color, #1989fa); }
.example-label { font-size: 14px; }
.example-hint { font-size: 11px; opacity: .6; margin-top: 10px; }
.notice { background: var(--secondary-color, #f5f5f5); padding: 12px 14px; border-radius: 6px; font-size: 13px; line-height: 1.8; margin-bottom: 14px; }
.notice-link { color: var(--primary-color, #1989fa); }
.scope-note { opacity: .6; font-size: 11px; line-height: 1.7; padding: 0 0 18px; }
.thinking { font-size: 13px; opacity: .7; padding-bottom: 20px; }
.error { border-left: 3px solid #d97706; padding: 10px 12px; font-size: 13px; line-height: 1.8; background: var(--secondary-color, #f5f5f5); margin-bottom: 12px; }
@media (max-width: 420px) { .conversation { padding: 16px; } .heading { font-size: 25px; } .welcome { padding-top: 8px; } .example { padding: 13px; } }
</style>

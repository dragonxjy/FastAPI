<script setup>
const input = defineModel({ type: String, default: '' })
defineProps({ busy: Boolean, canSend: Boolean })
const emit = defineEmits(['send'])

function onKeydown(event) {
  // 中文输入法按 Enter 是选字；Shift + Enter 换行，都不能误发送。
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing && event.keyCode !== 229) {
    event.preventDefault()
    emit('send')
  }
}
</script>

<template>
  <form class="composer" @submit.prevent="emit('send')">
    <label for="agent-input" class="input-label">告诉助手，你想如何处理文章</label>
    <textarea id="agent-input" v-model="input" class="input" rows="3" maxlength="4000"
      placeholder="例如：查找包含“技术”的文章，列出文章 ID 和标题"
      :disabled="busy" @keydown="onKeydown"></textarea>
    <div class="composer-footer">
      <span class="hint">Enter 发送 · Shift + Enter 换行</span>
      <button class="send" type="submit" :disabled="!canSend">{{ busy ? '正在处理…' : '发送' }}</button>
    </div>
  </form>
</template>

<style scoped>
.composer { margin: 0 18px 14px; padding: 12px; border: 1px solid color-mix(in srgb, currentColor 22%, transparent); border-radius: 12px; }
.composer:focus-within { border-color: var(--primary-color, #1989fa); }
.input-label { display: block; font-size: 12px; opacity: .75; margin-bottom: 8px; }
.input { width: 100%; resize: vertical; min-height: 66px; max-height: 160px; border: 0; outline: 0; font: inherit; font-size: 15px; line-height: 1.6; color: inherit; background: transparent; }
.composer-footer { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 8px; }
.hint { font-size: 11px; opacity: .6; }
.send { border: 0; padding: 9px 20px; border-radius: 6px; background: var(--primary-color, #1989fa); color: #fff; font-size: 14px; cursor: pointer; }
.send:disabled { opacity: .45; cursor: not-allowed; }
.send:focus-visible { outline: 2px solid currentColor; outline-offset: 3px; }
@media (max-width: 420px) { .composer { margin: 0 12px 10px; } .hint { max-width: 160px; } }
</style>

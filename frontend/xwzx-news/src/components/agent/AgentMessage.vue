<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({ message: { type: Object, required: true } })
// 模型回复也是外部输入：Markdown 转成 HTML 后先清理，再显示。
const safeHtml = computed(() => DOMPurify.sanitize(marked.parse(props.message.content || ''), {
  USE_PROFILES: { html: true }, FORBID_TAGS: ['img'],
}))
const toolNames = {
  list_categories: '查看分类', search_articles: '查找文章', get_article: '读取文章',
  create_article: '新增文章', update_article: '修改文章', delete_article: '删除文章',
}
const toolCalls = computed(() => (props.message.toolCalls || []).map((call, index) => {
  let result = call.result
  if (typeof result === 'string') {
    try { result = JSON.parse(result) } catch { /* 非 JSON 结果保留原文。 */ }
  }
  const articles = result?.articles || (result?.article ? [result.article] : [])
  return {
    ...call, key: index, label: toolNames[call.name] || call.name,
    output: typeof result === 'string' ? result : JSON.stringify(result, null, 2),
    articles: call.name === 'delete_article' ? [] : articles.filter(item => Number.isInteger(item.id) && item.id > 0),
  }
}))
</script>

<template>
  <article class="message" :class="{ 'from-user': message.role === 'user' }">
    <p class="speaker">{{ message.role === 'user' ? '你' : '文章助手' }} <span v-if="message.failed">· 请求未完成</span></p>
    <div v-if="message.role === 'user'" class="bubble user-text">{{ message.content }}</div>
    <div v-else class="bubble">
      <div class="markdown" v-html="safeHtml"></div>
      <details v-if="toolCalls.length" class="tools">
        <summary>查看执行过程 · {{ toolCalls.length }} 次工具调用</summary>
        <section v-for="call in toolCalls" :key="call.key" class="tool">
          <p class="tool-title">{{ call.key + 1 }}. {{ call.label }}</p>
          <p class="tool-caption">传入参数</p>
          <pre class="tool-data">{{ JSON.stringify(call.args, null, 2) }}</pre>
          <p class="tool-caption">执行结果</p>
          <pre class="tool-data">{{ call.output }}</pre>
          <RouterLink v-for="article in call.articles" :key="article.id" class="article-link" :to="`/news/detail/${article.id}`">
            #{{ article.id }} · {{ article.title || '查看文章' }} →
          </RouterLink>
        </section>
      </details>
      <p v-if="message.articlesChanged" class="changed">文章数据已更新，可回首页查看。</p>
    </div>
  </article>
</template>

<style scoped>
.message { margin: 0 0 24px; max-width: 94%; }
.from-user { margin-left: auto; max-width: 86%; }
.speaker { font-size: 12px; opacity: .65; margin-bottom: 7px; }
.from-user .speaker { text-align: right; }
.bubble { font-size: 15px; line-height: 1.75; overflow-wrap: anywhere; }
.user-text { white-space: pre-wrap; background: var(--secondary-color, #f5f5f5); padding: 12px 16px; border-radius: 12px 12px 2px 12px; }
.tools { margin-top: 16px; padding-top: 10px; border-top: 1px solid color-mix(in srgb, currentColor 15%, transparent); font-size: 13px; }
.tools summary { cursor: pointer; color: var(--primary-color, #1989fa); }
.tool { margin-top: 14px; }
.tool-title { font-weight: 600; }
.tool-caption { font-size: 12px; opacity: .7; margin: 8px 0 3px; }
.tool-data { max-height: 240px; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; padding: 10px; background: var(--secondary-color, #f5f5f5); font: 12px/1.6 monospace; }
.article-link { display: block; margin-top: 8px; color: var(--primary-color, #1989fa); }
.changed { font-size: 12px; color: var(--primary-color, #1989fa); margin-top: 12px; }
.markdown :deep(p) { margin: 0 0 10px; }
.markdown :deep(ul), .markdown :deep(ol) { padding-left: 24px; }
.markdown :deep(pre) { overflow: auto; padding: 12px; background: var(--secondary-color, #f5f5f5); }
.markdown :deep(code) { font-size: 13px; }
.markdown :deep(a) { color: var(--primary-color, #1989fa); text-decoration: underline; }
.markdown :deep(table) { display: block; max-width: 100%; overflow-x: auto; border-collapse: collapse; }
.markdown :deep(td), .markdown :deep(th) { border: 1px solid #999; padding: 6px; }
</style>

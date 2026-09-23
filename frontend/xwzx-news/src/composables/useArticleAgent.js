import { computed, onMounted, readonly, ref, shallowRef, watch } from 'vue'
import axios from 'axios'
import { apiConfig } from '../config/api'
import { useUserStore } from '../store/user'
import { useNewsStore } from '../store/modules/news'
import { useFavoriteStore } from '../store/modules/favorite'
import { useHistoryStore } from '../store/modules/history'

// 这里只处理聊天状态与请求；页面和消息样式放在 components/agent 中。
export function useArticleAgent() {
  const userStore = useUserStore()
  const newsStore = useNewsStore()
  const favoriteStore = useFavoriteStore()
  const historyStore = useHistoryStore()
  const messages = ref([])
  const input = shallowRef('')
  const busy = shallowRef(false)
  const error = shallowRef('')
  const status = shallowRef(null)
  const statusLoading = shallowRef(false)
  const statusError = shallowRef('')
  let nextId = 1

  const loggedIn = computed(() => Boolean(userStore.getLoginStatus && userStore.token))
  const canSend = computed(() => loggedIn.value && status.value?.configured && !busy.value && Boolean(input.value.trim()))

  async function checkStatus() {
    if (statusLoading.value) return
    statusLoading.value = true
    statusError.value = ''
    try {
      const response = await axios.get(`${apiConfig.baseURL}/api/agent/status`, { timeout: 10000 })
      if (response.data.code !== 200) throw new Error('状态读取失败')
      status.value = response.data.data
    } catch {
      status.value = null
      statusError.value = '连接不到文章助手，请确认后端已启动。'
    } finally {
      statusLoading.value = false
    }
  }

  // Agent 修改的是数据库；同步刷新首页、收藏和历史，避免继续显示旧文章。
  async function refreshArticles() {
    newsStore.newsDetail = {}
    newsStore.newsList = []
    await Promise.allSettled([
      newsStore.refreshNews(),
      favoriteStore.getFavoriteListApi({ refresh: true }),
      historyStore.getHistoryListApi({ refresh: true }),
    ])
    // 浏览器禁用本地存储时，也不能把已成功的聊天误报为失败。
    try {
      favoriteStore.saveFavorites()
      historyStore.saveHistory()
    } catch { /* 数据库结果仍有效，下次打开列表会重新加载。 */ }
  }

  async function send() {
    if (!canSend.value) return
    const message = input.value.trim()
    // 上下文最多 10 轮、合计 30000 字。失败消息不再发给模型。
    const history = messages.value.filter(item => !item.failed).slice(-20)
      .map(item => ({ role: item.role, content: item.content.slice(0, 20000) }))
    while (history.reduce((sum, item) => sum + item.content.length, 0) > 30000) history.shift()
    const userMessage = { id: nextId++, role: 'user', content: message }
    messages.value.push(userMessage)
    input.value = ''
    error.value = ''
    busy.value = true
    try {
      const response = await axios.post(`${apiConfig.baseURL}/api/agent/chat`, { message, history }, {
        headers: { Authorization: userStore.token }, timeout: 180000,
      })
      if (response.data.code !== 200) throw new Error(response.data.message || '请求未完成')
      const data = response.data.data
      messages.value.push({
        id: nextId++, role: 'assistant', content: data.reply,
        toolCalls: data.tool_calls || [], articlesChanged: data.articles_changed,
      })
      // 刷新列表在后台进行，不阻塞下一条聊天。
      if (data.articles_changed) void refreshArticles()
    } catch (err) {
      // 通过响应式数组修改，页面会立即显示失败状态。
      const failed = messages.value.find(item => item.id === userMessage.id)
      if (failed) failed.failed = true
      input.value = message
      const response = err.response?.data
      const detail = typeof response?.detail === 'string' ? response.detail : response?.message
      if (err.response?.status === 401) {
        userStore.logout()
        error.value = '登录已失效，请重新登录后继续。'
      } else {
        error.value = detail || (err.code === 'ECONNABORTED'
          ? '等待回复超时。请先查询文章是否已改变，再决定是否重新发送。'
          : '本次请求未完成。请检查后端或网络；涉及修改时，请先查询结果，避免重复操作。')
      }
      // 网络中断时后台也可能已执行工具，所以仍刷新文章数据。
      void refreshArticles()
    } finally {
      busy.value = false
    }
  }

  function clearChat() {
    if (busy.value) return
    messages.value = []
    error.value = ''
    input.value = ''
  }

  // 切换账号后清掉聊天内容；聊天不写入 localStorage。
  // 同步观察令牌：401 处理期间 busy 仍为 true，保留错误提示和待重试输入。
  watch(() => userStore.token, () => { if (!busy.value) clearChat() }, { flush: 'sync' })
  onMounted(checkStatus)
  return {
    messages: readonly(messages), input, busy: readonly(busy), error: readonly(error),
    status: readonly(status), statusLoading: readonly(statusLoading), statusError: readonly(statusError),
    loggedIn, canSend, checkStatus, send, clearChat,
  }
}

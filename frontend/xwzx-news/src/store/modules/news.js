import { defineStore } from 'pinia'
import axios from 'axios'
import { apiConfig } from '../../config/api'

// 进行中的列表请求（模块级，用于并发调用去重，不放入 state 避免序列化）
let listInFlight = null

// 将后端 snake_case 字段统一映射为前端使用的 camelCase 结构
const normalizeNews = (item) => ({
  id: item.id,
  title: item.title,
  description: item.description,
  content: item.content,
  image: item.image,
  author: item.author,
  views: item.views,
  categoryId: item.category_id ?? item.categoryId,
  publishTime: item.publish_time
    ? new Date(item.publish_time).toLocaleString()
    : item.publishTime
})

export const useNewsStore = defineStore('news', {
  state: () => ({
    newsList: [],
    newsDetail: {},
    categories: [],
    currentCategory: 1,
    page: 1,
    pageSize: 10,
    total: 0,
    loading: false,
    refreshing: false,
    finished: false,
    categoriesLoading: false,
    // 请求序号：用于丢弃刷新/切换分类前的过期响应
    requestSeq: 0
  }),

  actions: {
    // 获取新闻分类（加载中 / 已加载过则不重复请求）
    async getCategories() {
      if (this.categoriesLoading) return
      if (this.categories.length > 0) return

      this.categoriesLoading = true

      try {
        const response = await axios.get(`${apiConfig.baseURL}/api/news/categories`)

        if (response.data && response.data.code === 200) {
          this.categories = [...response.data.data, { id: 10, name: '更多' }]

          // 当前分类不在分类列表中时，默认选中第一个分类
          const exists = this.categories.some(item => item.id === this.currentCategory)
          if (!exists && this.categories.length > 0) {
            this.currentCategory = this.categories[0].id
          }
        }
      } catch (error) {
        console.error('获取新闻分类失败:', error)
        // 请求失败时使用默认分类兜底
        this.categories = [
          { id: 1, name: '头条' },
          { id: 2, name: '社会' },
          { id: 3, name: '国内' },
          { id: 4, name: '国际' },
          { id: 5, name: '娱乐' },
          { id: 6, name: '体育' },
          { id: 7, name: '科技' }
        ]
      } finally {
        this.categoriesLoading = false
      }
    },

    // 切换新闻分类（相同分类不重复请求）
    changeCategory(categoryId) {
      if (this.currentCategory === categoryId && this.newsList.length > 0) return

      this.currentCategory = categoryId
      this.newsList = []
      this.page = 1
      this.total = 0
      this.finished = false
      this.getNewsList(true)
    },

    // 下拉刷新：先确保分类已加载，再重置分页拉取第一页
    async refreshNews() {
      await this.getCategories()
      await this.getNewsList(true)
    },

    // 获取新闻列表（isRefresh=true 表示重置到第一页）
    async getNewsList(isRefresh = false) {
      // 分页加载：已全部加载完则停止；已有请求在途则复用同一个 Promise，
      // 避免 van-list 的 v-model 先置 loading=true 导致请求被拦截/重复发起
      if (!isRefresh) {
        if (this.finished) return
        if (listInFlight) return listInFlight
      }

      const task = (async () => {
        if (isRefresh) {
          this.page = 1
          this.total = 0
          this.finished = false
          this.refreshing = true
        }

        this.loading = true
        const requestSeq = ++this.requestSeq

        try {
          const params = {
            categoryId: this.currentCategory,
            page: this.page,
            pageSize: this.pageSize
          }

          const response = await axios.get(`${apiConfig.baseURL}/api/news/list`, { params })

          // 期间发生过刷新/切换分类，丢弃过期响应
          if (requestSeq !== this.requestSeq) return

          const res = response.data
          if (res && res.code === 200) {
            // 后端返回结构为 { code, total, data: [...], hasMore }，data 直接是数组
            const rawList = Array.isArray(res.data) ? res.data : (res.data?.list || [])
            const newsData = rawList.map(normalizeNews)

            if (Number.isFinite(res.total)) this.total = res.total
            this.newsList = isRefresh ? newsData : [...this.newsList, ...newsData]
            this.page += 1

            // 满足任一条件即判定加载结束：后端声明无更多、本页不足一页（含空页）、已达总数
            this.finished =
              res.hasMore === false ||
              newsData.length < this.pageSize ||
              (this.total > 0 && this.newsList.length >= this.total)
          }
        } catch (error) {
          console.error('获取新闻列表失败:', error)
        } finally {
          // 仅最新一次请求可以复位加载状态，避免旧请求覆盖新状态
          if (requestSeq === this.requestSeq) {
            this.loading = false
            this.refreshing = false
          }
        }
      })()

      listInFlight = task
      try {
        await task
      } finally {
        // 刷新会把 listInFlight 指向更新的请求，旧请求完成时不清理
        if (listInFlight === task) listInFlight = null
      }
    },

    // 获取新闻详情（含 relatedNews 相关推荐）
    async getNewsDetail(id) {
      const newsId = Number(id)

      try {
        const response = await axios.get(`${apiConfig.baseURL}/api/news/detail`, {
          params: { newsId }
        })

        const res = response.data
        if (res && res.code === 200 && res.data) {
          const detail = normalizeNews(res.data)
          // 相关推荐：结构与列表一致，统一做字段映射，不分页
          detail.relatedNews = Array.isArray(res.data.relatedNews)
            ? res.data.relatedNews.map(normalizeNews)
            : []
          this.newsDetail = detail
          return this.newsDetail
        }
      } catch (error) {
        console.error('获取新闻详情失败:', error)
      }

      // 兜底：接口失败时使用列表中已加载的数据
      const existing = this.newsList.find(item => item.id === newsId)
      if (existing) {
        this.newsDetail = { ...existing, relatedNews: [] }
        return this.newsDetail
      }
    },

    // 获取分类名称
    getCategoryName(categoryId) {
      const category = this.categories.find(item => item.id === categoryId)
      return category ? category.name : '未知'
    }
  }
})

import { defineStore } from 'pinia';
import axios from 'axios';
import { useUserStore } from '../user';
import { apiConfig } from '../../config/api';

// 时间格式化为本地时间字符串
const formatDateTime = (value) => {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
};

// 浏览历史列表项字段归一化：后端别名输出 publishedTime/viewTime，统一成页面使用的字段
const normalizeHistory = (item) => ({
  ...item,
  categoryId: item.categoryId ?? item.category_id,
  publishTime: formatDateTime(item.publishTime || item.publishedTime || item.publish_time),
  viewTime: formatDateTime(item.viewTime || item.view_time),
  historyId: item.historyId ?? item.history_id,
});

// 列表请求的进行中 Promise（并发去重）与请求序号（刷新时作废旧请求）
let historyListRequest = null;
let historyRequestSeq = 0;

export const useHistoryStore = defineStore('history', {
  state: () => ({
    history: [],
    // 浏览历史列表分页状态
    listLoading: true,
    page: 1,
    pageSize: 10,
    hasMore: true,
  }),
  
  getters: {
    getHistory: (state) => state.history,
  },
  
  actions: {
    // 添加浏览历史 - API请求
    async addHistoryApi(newsId) {
      const userStore = useUserStore();
      
      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        return { success: false, message: '请先登录' };
      }
      
      try {
        const response = await axios.post(`${apiConfig.baseURL}/api/history/add`, 
          { newsId },
          { 
            headers: { 
              Authorization: userStore.token 
            } 
          }
        );
        
        if (response.data.code === 200) {
          return { success: true, data: response.data.data };
        } else {
          return { success: false, message: response.data.message || '添加浏览历史失败' };
        }
      } catch (error) {
        console.error('添加浏览历史请求失败:', error);
        return { success: false, message: '网络请求失败' };
      }
    },
    
    // 添加浏览历史 - 本地
    addHistory(news) {
      // 检查是否已存在相同ID的新闻
      const existingIndex = this.history.findIndex(item => item.id === news.id);
      
      // 如果已存在，先删除旧记录
      if (existingIndex !== -1) {
        this.history.splice(existingIndex, 1);
      }
      
      // 添加到历史记录的最前面（最新浏览的在最前面）
      this.history.unshift({
        ...news,
        viewTime: new Date().toLocaleString()
      });
      
      // 限制历史记录数量，最多保存50条
      if (this.history.length > 50) {
        this.history.pop();
      }
      
      // 保存到本地存储
      this.saveHistory();
    },
    
    // 清空浏览历史
    clearHistory() {
      this.history = [];
      this.page = 1;
      this.hasMore = false;
      this.listLoading = false;
      this.saveHistory();
    },
    
    // 清空浏览历史 - API请求
    async clearHistoryApi() {
      const userStore = useUserStore();
      
      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        console.log('清空浏览历史API：用户未登录，使用本地操作');
        this.clearHistory();
        return { success: true, isLocal: true };
      }
      
      try {
        console.log('清空浏览历史API：开始请求');
        const response = await axios.delete(`${apiConfig.baseURL}/api/history/clear`, { 
          headers: { 
            Authorization: userStore.token 
          } 
        });
        
        if (response.data.code === 200) {
          console.log('清空浏览历史API：清空成功');
          // 更新本地历史记录
          this.clearHistory();
          return { success: true };
        } else {
          console.error('清空浏览历史API：请求失败', response.data.message);
          return { success: false, message: response.data.message || '清空浏览历史失败' };
        }
      } catch (error) {
        console.error('清空浏览历史API：请求异常', error);
        return { success: false, message: '网络请求失败' };
      }
    },
    
    // 删除单条浏览历史
    removeHistory(id) {
      this.history = this.history.filter(item => item.id !== id);
      this.saveHistory();
    },
    
    // 删除单条浏览历史 - API请求
    async removeHistoryApi(id) {
      const userStore = useUserStore();
      
      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        console.log('删除浏览历史API：用户未登录，使用本地操作');
        this.removeHistory(id);
        return { success: true, isLocal: true };
      }
      
      try {
        console.log('删除浏览历史API：开始请求', id);
        const response = await axios.delete(`${apiConfig.baseURL}/api/history/delete/${id}`, { 
          headers: { 
            Authorization: userStore.token 
          } 
        });
        
        if (response.data.code === 200) {
          console.log('删除浏览历史API：删除成功');
          // 更新本地历史记录
          this.removeHistory(id);
          return { success: true };
        } else {
          console.error('删除浏览历史API：请求失败', response.data.message);
          return { success: false, message: response.data.message || '删除浏览历史失败' };
        }
      } catch (error) {
        console.error('删除浏览历史API：请求异常', error);
        return { success: false, message: '网络请求失败' };
      }
    },
    
    // 保存到本地存储
    saveHistory() {
      localStorage.setItem('news_history', JSON.stringify(this.history));
    },
    
    // 从本地存储加载
    loadHistory() {
      const savedHistory = localStorage.getItem('news_history');
      if (savedHistory) {
        this.history = JSON.parse(savedHistory);
      }
    },
    
    // 获取浏览历史 - API请求（分页追加，hasMore 控制是否还有下一页）
    // options.refresh=true 时重置到第 1 页（首次进入/手动刷新）
    async getHistoryListApi(options = {}) {
      const { refresh = false } = options;
      const userStore = useUserStore();
      
      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        console.log('获取浏览历史API：用户未登录，使用本地数据');
        this.listLoading = false;
        this.hasMore = false;
        return { success: false, message: '请先登录', isLocal: true };
      }

      // 刷新：重置分页并作废旧请求，避免旧响应覆盖新数据
      if (refresh) {
        historyRequestSeq += 1;
        this.page = 1;
        this.hasMore = true;
        this.history = [];
        this.listLoading = true;
      }

      // 非刷新的并发触发（van-list 自动检查等）复用进行中的同一请求
      if (historyListRequest && !refresh) {
        return historyListRequest;
      }

      const seq = historyRequestSeq;
      const currentPage = this.page;
      this.listLoading = true;

      const request = axios
        .get(`${apiConfig.baseURL}/api/history/list`, {
          params: {
            page: currentPage,
            pageSize: this.pageSize
          },
          headers: {
            Authorization: userStore.token
          }
        })
        .then((response) => {
          // 已被刷新作废的旧响应直接丢弃
          if (seq !== historyRequestSeq) {
            return { success: false, stale: true };
          }

          if (response.data.code === 200) {
            const data = response.data.data || {};
            const historyList = Array.isArray(data.list) ? data.list.map(normalizeHistory) : [];

            if (currentPage === 1) {
              this.history = historyList;
            } else {
              // 按 id 去重后追加
              const existIds = new Set(this.history.map(item => item.id));
              this.history = [...this.history, ...historyList.filter(item => !existIds.has(item.id))];
            }

            this.page = currentPage + 1;
            // 以后端 hasMore 为准（别名输出，兼容 has_more）
            this.hasMore = data.hasMore === true || data.has_more === true;
            // 保存到本地存储
            this.saveHistory();
            return { success: true, data };
          }
          return { success: false, message: response.data.message || '获取浏览历史失败' };
        })
        .catch((error) => {
          if (seq !== historyRequestSeq) {
            return { success: false, stale: true };
          }
          console.error('获取浏览历史API：请求异常', error);
          return { success: false, message: '网络请求失败' };
        })
        .finally(() => {
          if (historyListRequest === request) {
            historyListRequest = null;
          }
          if (seq === historyRequestSeq) {
            this.listLoading = false;
          }
        });

      historyListRequest = request;
      return request;
    },
  },
});
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

// 收藏列表项字段归一化：后端别名输出 publishedTime/favoriteTime，统一成页面使用的字段
const normalizeFavorite = (item) => ({
  ...item,
  categoryId: item.categoryId ?? item.category_id,
  publishTime: formatDateTime(item.publishTime || item.publishedTime || item.publish_time),
  favoriteTime: formatDateTime(item.favoriteTime || item.favorite_time),
  favoriteId: item.favoriteId ?? item.favorite_id,
});

// 列表请求的进行中 Promise（并发去重）与请求序号（刷新时作废旧请求）
let favoriteListRequest = null;
let favoriteRequestSeq = 0;

export const useFavoriteStore = defineStore('favorite', {
  state: () => ({
    favorites: [],
    loading: false,
    // 收藏列表分页状态
    listLoading: true,
    page: 1,
    pageSize: 10,
    hasMore: true,
  }),
  
  getters: {
    getFavorites: (state) => state.favorites,
    isFavorite: (state) => (id) => state.favorites.some(item => item.id === id),
  },
  
  actions: {
    // 检查文章收藏状态 - API请求
    async checkFavoriteStatusApi(newsId) {
      const userStore = useUserStore(); 
      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        // return { success: false, message: '请先登录' };
        console.log('用户未登录，返回本地状态');
        return { 
          success: true, 
          isFavorite: this.isFavorite(newsId),
          isLocal: true
        };
      }
      else{
      
        try {
          this.loading = true;
          const response = await axios.get(`${apiConfig.baseURL}/api/favorite/check`, { 
            headers: { 
              Authorization:`${userStore.token}` 
            },
            params: { newsId }
          });
          
          if (response.data.code === 200) {
            return { 
              success: true, 
              isFavorite: response.data.data.isFavorite 
            };
          } else {
            return { success: false, message: response.data.message || '获取收藏状态失败' };
          }
        } catch (error) {
          console.error('检查收藏状态请求失败:', error);
          // 如果API请求失败，回退到本地状态检查
          return { 
            success: true, 
            isFavorite: this.isFavorite(newsId),
            isLocal: true
          };
        } finally {
          this.loading = false;
        }
    }
    },
    
    // 添加收藏 - API请求
    async addFavoriteApi(newsId) {
      const userStore = useUserStore();
      
      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        return { success: false, message: '请先登录' };
      }
      
      try {
        this.loading = true;
        const response = await axios.post(`${apiConfig.baseURL}/api/favorite/add`, 
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
          return { success: false, message: response.data.message || '收藏失败' };
        }
      } catch (error) {
        console.error('添加收藏请求失败:', error);
        return { success: false, message: '网络请求失败' };
      } finally {
        this.loading = false;
      }
    },
    
    // 取消收藏 - API请求
    async removeFavoriteApi(newsId) {
      const userStore = useUserStore();
      
      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        return { success: false, message: '请先登录' };
      }
      
      try {
        this.loading = true;
        const response = await axios.delete(`${apiConfig.baseURL}/api/favorite/remove?newsId=${newsId}`, { 
          headers: { 
            Authorization: userStore.token 
          }
        });
        
        if (response.data.code === 200) {
          return { success: true };
        } else {
          return { success: false, message: response.data.message || '取消收藏失败' };
        }
      } catch (error) {
        console.error('取消收藏请求失败:', error);
        return { success: false, message: '网络请求失败' };
      } finally {
        this.loading = false;
      }
    },
    
    // 添加收藏 - 本地
    addFavorite(news) {
      // 检查是否已存在相同ID的新闻
      if (!this.isFavorite(news.id)) {
        // 添加到收藏列表
        this.favorites.unshift({
          ...news,
          favoriteTime: new Date().toLocaleString()
        });
        
        // 保存到本地存储
        this.saveFavorites();
      }
    },
    
    // 取消收藏 - 本地
    removeFavorite(id) {
      this.favorites = this.favorites.filter(item => item.id !== id);
      this.saveFavorites();
    },
    
    // 切换收藏状态 - 结合API和本地
    async toggleFavorite(news) {
      // 确保news对象存在且有id属性
      if (!news || !news.id) {
        console.error('无效的新闻对象:', news);
        return null;
      }
      
      if (this.isFavorite(news.id)) {
        // 取消收藏
        const result = await this.removeFavoriteApi(news.id);
        if (result.success) {
          this.removeFavorite(news.id);
          return false;
        } else {
          return null; // 返回null表示操作失败
        }
      } else {
        // 添加收藏
        const result = await this.addFavoriteApi(news.id);
        if (result.success) {
          this.addFavorite(news);
          return true;
        } else {
          return null; // 返回null表示操作失败
        }
      }
    },
    
    
    // 清空收藏
    clearFavorites() {
      this.favorites = [];
      this.page = 1;
      this.hasMore = false;
      this.listLoading = false;
      this.saveFavorites();
    },
    
    // 清空收藏 - API请求
    async clearFavoritesApi() {
      const userStore = useUserStore();
      
      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        return { success: false, message: '请先登录' };
      }
      
      try {
        this.loading = true;
        const response = await axios.delete(`${apiConfig.baseURL}/api/favorite/clear`, { 
          headers: { 
            Authorization: userStore.token 
          }
        });
        
        if (response.data.code === 200) {
          // 清空本地收藏列表
          this.clearFavorites();
          return { success: true };
        } else {
          return { success: false, message: response.data.message || '清空收藏失败' };
        }
      } catch (error) {
        console.error('清空收藏请求失败:', error);
        return { success: false, message: '网络请求失败' };
      } finally {
        this.loading = false;
      }
    },
    
    // 保存到本地存储
    saveFavorites() {
      localStorage.setItem('news_favorites', JSON.stringify(this.favorites));
    },
    
    // 从本地存储加载
    loadFavorites() {
      const savedFavorites = localStorage.getItem('news_favorites');
      if (savedFavorites) {
        this.favorites = JSON.parse(savedFavorites);
      }
    },
    
    // 获取收藏列表 - API请求（分页追加，hasMore 控制是否还有下一页）
    // options.refresh=true 时重置到第 1 页（首次进入/下拉刷新）
    async getFavoriteListApi(options = {}) {
      const { refresh = false } = options;
      const userStore = useUserStore();

      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        this.listLoading = false;
        return { success: false, message: '请先登录' };
      }

      // 刷新：重置分页并作废旧请求，避免旧响应覆盖新数据
      if (refresh) {
        favoriteRequestSeq += 1;
        this.page = 1;
        this.hasMore = true;
        this.favorites = [];
        this.listLoading = true;
      }

      // 非刷新的并发触发（van-list 自动检查等）复用进行中的同一请求
      if (favoriteListRequest && !refresh) {
        return favoriteListRequest;
      }

      const seq = favoriteRequestSeq;
      const currentPage = this.page;
      this.listLoading = true;

      const request = axios
        .get(`${apiConfig.baseURL}/api/favorite/list`, {
          headers: {
            Authorization: userStore.token
          },
          params: { page: currentPage, pageSize: this.pageSize }
        })
        .then((response) => {
          // 已被刷新作废的旧响应直接丢弃
          if (seq !== favoriteRequestSeq) {
            return { success: false, stale: true };
          }

          if (response.data.code === 200) {
            const data = response.data.data || {};
            const list = Array.isArray(data.list) ? data.list.map(normalizeFavorite) : [];

            if (currentPage === 1) {
              this.favorites = list;
            } else {
              // 按 id 去重后追加
              const existIds = new Set(this.favorites.map(item => item.id));
              this.favorites = [...this.favorites, ...list.filter(item => !existIds.has(item.id))];
            }

            this.page = currentPage + 1;
            this.hasMore = data.hasMore === true;
            return { success: true, data };
          }
          return { success: false, message: response.data.message || '获取收藏列表失败' };
        })
        .catch((error) => {
          if (seq !== favoriteRequestSeq) {
            return { success: false, stale: true };
          }
          console.error('获取收藏列表请求失败:', error);
          return { success: false, message: '网络请求失败' };
        })
        .finally(() => {
          if (favoriteListRequest === request) {
            favoriteListRequest = null;
          }
          if (seq === favoriteRequestSeq) {
            this.listLoading = false;
          }
        });

      favoriteListRequest = request;
      return request;
    },
  },
});
<template>
  <div class="home">
    <van-nav-bar :title="$t('home.title')" fixed />
    
    <!-- 更多选项独立div -->
    <div class="more-options">
      <div class="more-tab" @click="goToCategory">
        {{ $t('home.more') }} <van-icon name="arrow" />
      </div>
    </div>
    
    <div class="category-tabs">
      <van-tabs v-model:active="activeTab" sticky swipeable animated>
        <van-tab 
          v-for="(category, index) in displayCategories" 
          :key="category.id" 
          :title="getCategoryTranslation(category.name)"
        >
          <!-- 只渲染当前激活 tab 的列表，避免多个 van-list 实例共享 loading 状态互相触发加载 -->
          <van-pull-refresh v-if="index === activeTab" v-model="newsStore.refreshing" @refresh="onRefresh">
            <van-list
              v-model:loading="newsStore.loading"
              :finished="newsStore.finished"
              :finished-text="$t('home.noMore')"
              @load="onLoad"
            >
              <news-item 
                v-for="item in newsStore.newsList" 
                :key="item.id" 
                :news="item" 
              />
            </van-list>
          </van-pull-refresh>
        </van-tab>
      </van-tabs>
    </div>
    
    <tab-bar />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, onBeforeUnmount } from 'vue'
import { useNewsStore } from '../store/modules/news'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import NewsItem from '../components/NewsItem.vue'
import TabBar from '../components/TabBar.vue'

const newsStore = useNewsStore()
const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const activeTab = ref(0)
const tabsTop = ref(0)

// 根据分类ID同步激活 tab 的索引
const syncActiveTab = (categoryId) => {
  const index = newsStore.categories.findIndex(
    cat => cat.name !== '更多' && cat.id === categoryId
  )
  if (index !== -1) {
    activeTab.value = index
  }
}

// 监听路由变化：只同步激活的 tab，分类切换统一由 watch(activeTab) 处理
watch(
  () => route.query.categoryId,
  (newCategoryId) => {
    if (!newCategoryId) return
    syncActiveTab(parseInt(newCategoryId))
  },
  { immediate: true }
)

onMounted(async () => {
  // 先获取分类，再加载列表（确定性初始化，不依赖 van-list 的自动检查时机）
  await newsStore.getCategories()

  if (route.query.categoryId) {
    // 从分类页跳转过来：同步 tab 后由 watch(activeTab) 自动切换分类并拉取列表
    syncActiveTab(parseInt(route.query.categoryId))
  } else {
    // 常规进入：显式拉取第一页（与 van-list 的自动 @load 会被 store 去重，不会重复请求）
    newsStore.getNewsList()
  }

  // 初始化位置
  setTimeout(updateTabsPosition, 300)

  // 添加滚动事件监听
  window.addEventListener('scroll', handleScroll)
})

// 计算属性：显示的分类（只显示非"更多"分类）
const displayCategories = computed(() => {
  // 获取所有非"更多"分类
  return newsStore.categories.filter(category => category.name !== '更多');
})

// 获取分类名称的翻译
const getCategoryTranslation = (categoryName) => {
  const categoryMap = {
    '头条': 'headline',
    '社会': 'society',
    '国内': 'domestic',
    '国际': 'international',
    '娱乐': 'entertainment',
    '体育': 'sports',
    '军事': 'military',
    '科技': 'technology',
    '财经': 'finance',
    '更多': 'more'
  };
  
  const key = categoryMap[categoryName];
  return key ? t(`home.categories.${key}`) : categoryName;
}
    

// 跳转到分类页面
const goToCategory = () => {
  router.push('/category')
}

// 获取分类导航栏的位置并设置滚动监听
const updateTabsPosition = () => {
  const tabsElement = document.querySelector('.van-tabs__wrap')
  if (tabsElement) {
    tabsTop.value = tabsElement.getBoundingClientRect().top
  }
}

// 滚动事件处理
const handleScroll = () => {
  updateTabsPosition()
}

// 组件销毁前移除事件监听
onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
})

// tab 切换（点击或滑动）时切换分类；store 内部会拦截相同分类的重复请求
watch(activeTab, (newVal) => {
  const categoryId = newsStore.categories[newVal]?.id
  if (categoryId) {
    newsStore.changeCategory(categoryId)
  }
})

// 下拉刷新：先获取分类，再重置列表拉取第一页
const onRefresh = () => {
  newsStore.refreshNews()
}

// 上拉加载更多（store 内部对并发请求自动去重）
const onLoad = () => {
  newsStore.getNewsList()
}
</script>

<style scoped>
.home {
  padding-top: 46px;
  padding-bottom: 50px;
  background-color: #f7f8fa;
  min-height: 100vh;
}

.category-tabs {
  margin-bottom: 10px;
  position: relative;
}

:deep(.van-tabs__wrap) {
  background-color: #fff;
}

:deep(.van-tab) {
  font-size: 14px;
}

:deep(.van-tab--active) {
  font-weight: bold;
  color: #1989fa;
}

.more-options {
  position: fixed;
  right: 0;
  background-color: #fff;
  padding: 0;
  border-radius: 4px 0 0 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  /* 通过计算属性动态设置top */
  top: v-bind('tabsTop + "px"');
  height: 44px; /* 与van-tabs__wrap高度一致 */
  display: flex;
  align-items: center;
}

.more-tab {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #1989fa;
  font-weight: bold;
  height: 100%;
  padding: 0 10px;
}

.dropdown-menu {
  position: absolute;
  right: 15px;
  top: 40px;
  min-width: 100px;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  z-index: 999;
}

.dropdown-item {
  padding: 10px 15px;
  text-align: center;
  border-bottom: 1px solid #f5f5f5;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover {
  background-color: #f5f5f5;
}
</style>
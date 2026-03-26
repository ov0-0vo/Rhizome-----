<template>
  <div class="app" :data-theme="theme">
    <button class="mobile-menu-btn" @click="sidebarOpen = true">
      <span class="menu-icon">☰</span>
    </button>

    <div class="sidebar-overlay" v-if="sidebarOpen" @click="sidebarOpen = false"></div>

    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-header">
        <h1 class="logo">
          <span class="logo-icon">🌳</span>
          <span class="logo-text">Rhizome</span>
        </h1>
        <button class="close-btn" @click="sidebarOpen = false">×</button>
      </div>

      <nav class="nav-menu">
        <div 
          class="nav-item" 
          :class="{ active: activeTab === 'chat' }"
          @click="selectTab('chat')"
        >
          <span class="nav-icon">💬</span>
          <span class="nav-text">对话</span>
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeTab === 'catalog' }"
          @click="selectTab('catalog')"
        >
          <span class="nav-icon">📚</span>
          <span class="nav-text">知识目录</span>
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeTab === 'graph' }"
          @click="selectTab('graph')"
        >
          <span class="nav-icon">🕸️</span>
          <span class="nav-text">知识图谱</span>
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeTab === 'search' }"
          @click="selectTab('search')"
        >
          <span class="nav-icon">🔍</span>
          <span class="nav-text">搜索</span>
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeTab === 'stats' }"
          @click="selectTab('stats')"
        >
          <span class="nav-icon">📊</span>
          <span class="nav-text">统计</span>
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeTab === 'review' }"
          @click="selectTab('review')"
        >
          <span class="nav-icon">📖</span>
          <span class="nav-text">复习</span>
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeTab === 'config' }"
          @click="selectTab('config')"
        >
          <span class="nav-icon">⚙️</span>
          <span class="nav-text">配置</span>
        </div>
      </nav>

      <div class="sidebar-footer">
        <button class="theme-toggle" @click="toggleTheme">
          <span class="theme-icon">{{ theme === 'dark' ? '☀️' : '🌙' }}</span>
          <span class="theme-text">{{ theme === 'dark' ? '浅色模式' : '深色模式' }}</span>
        </button>
      </div>
    </aside>

    <main class="main-content">
      <transition name="fade" mode="out-in">
        <ChatView v-if="activeTab === 'chat'" key="chat" />
        <CatalogView v-else-if="activeTab === 'catalog'" key="catalog" />
        <GraphView v-else-if="activeTab === 'graph'" key="graph" />
        <SearchView v-else-if="activeTab === 'search'" key="search" />
        <StatsView v-else-if="activeTab === 'stats'" key="stats" />
        <ReviewView v-else-if="activeTab === 'review'" key="review" />
        <ConfigView v-else-if="activeTab === 'config'" key="config" />
      </transition>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ChatView from './views/ChatView.vue'
import CatalogView from './views/CatalogView.vue'
import GraphView from './views/GraphView.vue'
import SearchView from './views/SearchView.vue'
import StatsView from './views/StatsView.vue'
import ReviewView from './views/ReviewView.vue'
import ConfigView from './views/ConfigView.vue'

const activeTab = ref('chat')
const theme = ref('light')
const sidebarOpen = ref(false)

const selectTab = (tab) => {
  activeTab.value = tab
  sidebarOpen.value = false
}

const toggleTheme = () => {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem('theme', theme.value)
}

onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme) {
    theme.value = savedTheme
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    theme.value = 'dark'
  }
})
</script>

<style scoped>
.app {
  height: 100vh;
  display: flex;
  background: var(--bg-primary);
  transition: background-color var(--transition-normal);
  overflow: hidden;
}

.mobile-menu-btn {
  display: none;
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 200;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  box-shadow: var(--shadow-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mobile-menu-btn:hover {
  background: var(--bg-secondary);
}

.menu-icon {
  font-size: 20px;
  color: var(--text-primary);
}

.sidebar-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 250;
  backdrop-filter: blur(2px);
}

.sidebar {
  width: 240px;
  min-width: 240px;
  height: 100vh;
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-light);
  transition: all var(--transition-normal);
}

.sidebar-header {
  padding: 20px 16px;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.logo-icon {
  font-size: 26px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-3px);
  }
}

.logo-text {
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.close-btn {
  display: none;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-secondary);
  font-size: 24px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-menu {
  flex: 1;
  padding: 16px 12px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 4px;
  cursor: pointer;
  border-radius: var(--radius-lg);
  font-weight: 500;
  font-size: 14px;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  position: relative;
  user-select: none;
}

.nav-item:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.nav-item.active {
  color: var(--primary-color);
  background: var(--primary-light);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 24px;
  background: var(--primary-color);
  border-radius: 0 2px 2px 0;
}

.nav-icon {
  font-size: 18px;
  width: 24px;
  text-align: center;
}

.nav-text {
  flex: 1;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-light);
}

.theme-toggle {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 16px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.theme-toggle:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.theme-icon {
  font-size: 18px;
}

.main-content {
  flex: 1;
  min-width: 0;
  height: 100%;
  padding: 24px;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 768px) {
  .mobile-menu-btn {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .sidebar-overlay {
    display: block;
  }

  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: 300;
    transform: translateX(-100%);
    box-shadow: var(--shadow-lg);
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .close-btn {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .main-content {
    height: 100vh;
    padding: 0;
    padding-top: 60px;
    box-sizing: border-box;
  }
}
</style>

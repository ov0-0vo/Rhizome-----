<template>
  <div class="app" :data-theme="theme">
    <header class="header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="logo">
            <span class="logo-icon">🌳</span>
            <span class="logo-text">Rhizome</span>
            <span class="logo-subtitle">灵犀树</span>
          </h1>
        </div>
        <div class="header-right">
          <button class="btn-icon theme-toggle" @click="toggleTheme" :title="theme === 'dark' ? '切换到浅色模式' : '切换到深色模式'">
            <span v-if="theme === 'dark'">☀️</span>
            <span v-else>🌙</span>
          </button>
        </div>
      </div>
    </header>

    <main class="main-content">
      <div class="container">
        <nav class="tabs">
          <div 
            class="tab" 
            :class="{ active: activeTab === 'chat' }"
            @click="activeTab = 'chat'"
          >
            <span class="tab-icon">💬</span>
            <span class="tab-text">对话</span>
          </div>
          <div 
            class="tab" 
            :class="{ active: activeTab === 'catalog' }"
            @click="activeTab = 'catalog'"
          >
            <span class="tab-icon">📚</span>
            <span class="tab-text">知识目录</span>
          </div>
          <div 
            class="tab" 
            :class="{ active: activeTab === 'search' }"
            @click="activeTab = 'search'"
          >
            <span class="tab-icon">🔍</span>
            <span class="tab-text">搜索</span>
          </div>
          <div 
            class="tab" 
            :class="{ active: activeTab === 'stats' }"
            @click="activeTab = 'stats'"
          >
            <span class="tab-icon">📊</span>
            <span class="tab-text">统计</span>
          </div>
        </nav>

        <transition name="fade" mode="out-in">
          <ChatView v-if="activeTab === 'chat'" key="chat" />
          <CatalogView v-else-if="activeTab === 'catalog'" key="catalog" />
          <SearchView v-else-if="activeTab === 'search'" key="search" />
          <StatsView v-else-if="activeTab === 'stats'" key="stats" />
        </transition>
      </div>
    </main>

    <footer class="footer">
      <p>通过对话建立和管理您的个人知识体系</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ChatView from './views/ChatView.vue'
import CatalogView from './views/CatalogView.vue'
import SearchView from './views/SearchView.vue'
import StatsView from './views/StatsView.vue'

const activeTab = ref('chat')
const theme = ref('light')

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
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  transition: background-color var(--transition-normal);
}

.header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-light);
  transition: all var(--transition-normal);
}

[data-theme="dark"] .header {
  background: rgba(26, 29, 33, 0.85);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.logo-icon {
  font-size: 28px;
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

.logo-subtitle {
  font-size: 14px;
  font-weight: 400;
  color: var(--text-secondary);
  margin-left: 4px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-toggle {
  font-size: 18px;
}

.main-content {
  flex: 1;
  padding-bottom: 40px;
}

.tabs {
  display: flex;
  gap: 4px;
  background: var(--bg-secondary);
  padding: 6px;
  border-radius: var(--radius-xl);
  margin-bottom: 24px;
  box-shadow: var(--shadow-sm);
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  cursor: pointer;
  border-radius: var(--radius-lg);
  font-weight: 500;
  font-size: 14px;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  position: relative;
  user-select: none;
}

.tab:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.tab.active {
  color: var(--primary-color);
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
}

.tab-icon {
  font-size: 16px;
}

.footer {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
  font-size: 13px;
  border-top: 1px solid var(--border-light);
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
  .header-content {
    padding: 12px 16px;
  }
  
  .logo-subtitle {
    display: none;
  }
  
  .tab-text {
    display: none;
  }
  
  .tab {
    padding: 12px 16px;
  }
  
  .tab-icon {
    font-size: 20px;
  }
}
</style>

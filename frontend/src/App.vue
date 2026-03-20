<template>
  <div class="app">
    <header class="header">
      <div class="container">
        <h1 class="logo">
          <span class="logo-icon">🌳</span>
          Rhizome 灵犀树
        </h1>
        <p class="subtitle">通过对话建立和管理您的个人知识体系</p>
      </div>
    </header>

    <main class="container">
      <div class="tabs">
        <div 
          class="tab" 
          :class="{ active: activeTab === 'chat' }"
          @click="activeTab = 'chat'"
        >
          💬 对话
        </div>
        <div 
          class="tab" 
          :class="{ active: activeTab === 'catalog' }"
          @click="activeTab = 'catalog'"
        >
          📚 知识目录
        </div>
        <div 
          class="tab" 
          :class="{ active: activeTab === 'search' }"
          @click="activeTab = 'search'"
        >
          🔍 搜索
        </div>
        <div 
          class="tab" 
          :class="{ active: activeTab === 'stats' }"
          @click="activeTab = 'stats'"
        >
          📊 统计
        </div>
      </div>

      <ChatView v-if="activeTab === 'chat'" />
      <CatalogView v-else-if="activeTab === 'catalog'" />
      <SearchView v-else-if="activeTab === 'search'" />
      <StatsView v-else-if="activeTab === 'stats'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ChatView from './views/ChatView.vue'
import CatalogView from './views/CatalogView.vue'
import SearchView from './views/SearchView.vue'
import StatsView from './views/StatsView.vue'

const activeTab = ref('chat')
</script>

<style scoped>
.app {
  min-height: 100vh;
}

.header {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  padding: 30px 0;
  margin-bottom: 20px;
}

.logo {
  font-size: 28px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  font-size: 32px;
}

.subtitle {
  margin-top: 8px;
  opacity: 0.9;
  font-size: 14px;
}
</style>

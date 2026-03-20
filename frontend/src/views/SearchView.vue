<template>
  <div class="search-view">
    <div class="card">
      <h2>🔍 知识搜索</h2>
      
      <div class="search-input">
        <input
          v-model="query"
          @keydown.enter="search"
          placeholder="输入搜索关键词..."
          class="input"
        />
        <button 
          class="btn btn-primary" 
          @click="search"
          :disabled="loading || !query.trim()"
        >
          搜索
        </button>
      </div>

      <div v-if="loading" class="loading"></div>

      <div v-else-if="results.length > 0" class="results">
        <p class="result-count">找到 {{ results.length }} 条相关知识</p>
        
        <div 
          v-for="item in results" 
          :key="item.id" 
          class="result-item"
        >
          <h3 class="question">{{ item.question }}</h3>
          <p class="answer">{{ truncate(item.answer, 200) }}</p>
          <div class="meta">
            <span class="similarity">相似度: {{ (item.similarity * 100).toFixed(1) }}%</span>
            <span v-if="item.catalog_id" class="catalog">📁 {{ item.catalog_id }}</span>
          </div>
        </div>
      </div>

      <div v-else-if="searched" class="empty">
        未找到相关知识
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { knowledgeApi } from '../api'

const query = ref('')
const results = ref([])
const loading = ref(false)
const searched = ref(false)

const search = async () => {
  if (!query.value.trim()) return
  
  loading.value = true
  searched.value = true
  
  try {
    const response = await knowledgeApi.search(query.value)
    results.value = response.data
  } catch (error) {
    console.error('Search failed:', error)
  } finally {
    loading.value = false
  }
}

const truncate = (text, length) => {
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}
</script>

<style scoped>
.search-view {
  padding: 0;
}

.search-view h2 {
  margin-bottom: 20px;
}

.search-input {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.result-count {
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.result-item {
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 12px;
}

.question {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.answer {
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
}

.similarity {
  color: var(--primary-color);
}

.empty {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}
</style>

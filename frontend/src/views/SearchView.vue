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
          @click="selectedKnowledge = item"
        >
          <h3 class="question">{{ item.question }}</h3>
          <p class="answer">{{ truncate(item.answer, 200) }}</p>
          <div class="meta">
            <span class="similarity">相似度: {{ (item.similarity * 100).toFixed(1) }}%</span>
            <span v-if="item.keywords && item.keywords.length" class="keywords">
              {{ item.keywords.slice(0, 3).join(', ') }}
            </span>
          </div>
        </div>
      </div>

      <div v-else-if="searched" class="empty">
        未找到相关知识
      </div>
    </div>

    <div v-if="selectedKnowledge" class="knowledge-detail" @click.self="selectedKnowledge = null">
      <div class="detail-content">
        <div class="detail-header">
          <h3>{{ selectedKnowledge.question }}</h3>
          <button class="close-btn" @click="selectedKnowledge = null">×</button>
        </div>
        <div class="detail-body">
          <div class="detail-section">
            <strong>回答：</strong>
            <p>{{ selectedKnowledge.answer }}</p>
          </div>
          <div v-if="selectedKnowledge.keywords && selectedKnowledge.keywords.length" class="detail-section">
            <strong>关键词：</strong>
            <span class="keyword-tag" v-for="kw in selectedKnowledge.keywords" :key="kw">
              {{ kw }}
            </span>
          </div>
          <div class="detail-section">
            <strong>相似度：</strong>
            {{ (selectedKnowledge.similarity * 100).toFixed(1) }}%
          </div>
          <div class="detail-section">
            <strong>创建时间：</strong>
            {{ formatDate(selectedKnowledge.created_at) }}
          </div>
        </div>
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
const selectedKnowledge = ref(null)

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
  if (!text) return ''
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN')
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
  cursor: pointer;
  transition: all 0.2s;
}

.result-item:hover {
  border-color: var(--primary-color);
  background: var(--primary-light);
  transform: translateX(4px);
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

.keywords {
  color: var(--text-secondary);
}

.empty {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.knowledge-detail {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.detail-content {
  background: var(--card-bg);
  border-radius: 12px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.detail-header h3 {
  margin: 0;
  font-size: 18px;
  padding-right: 20px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: var(--text-primary);
}

.detail-body {
  padding: 20px;
}

.detail-section {
  margin-bottom: 16px;
}

.detail-section strong {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
}

.detail-section p {
  margin: 0;
  line-height: 1.6;
  white-space: pre-wrap;
}

.keyword-tag {
  display: inline-block;
  background: var(--primary-light);
  color: var(--primary-color);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 6px;
  margin-bottom: 4px;
}
</style>

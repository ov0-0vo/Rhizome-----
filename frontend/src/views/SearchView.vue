<template>
  <div class="search-view">
    <div class="card">
      <div class="card-header">
        <h2>🔍 知识搜索</h2>
      </div>
      
      <div class="search-input-wrapper">
        <div class="search-input">
          <span class="search-icon">🔍</span>
          <input
            v-model="query"
            @keydown.enter="search"
            placeholder="输入搜索关键词..."
            class="input search-text"
          />
          <button 
            class="btn btn-primary search-btn" 
            @click="search"
            :disabled="loading || !query.trim()"
          >
            <span class="btn-text">搜索</span>
            <span class="btn-icon">➤</span>
          </button>
        </div>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="skeleton skeleton-item"></div>
        <div class="skeleton skeleton-item"></div>
        <div class="skeleton skeleton-item"></div>
      </div>

      <div v-else-if="results.length > 0" class="results">
        <div class="result-header">
          <span class="result-count">找到 {{ results.length }} 条相关知识</span>
        </div>
        
        <div 
          v-for="(item, index) in results" 
          :key="item.id" 
          class="result-item"
          @click="selectedKnowledge = item"
          :style="{ animationDelay: `${index * 0.05}s` }"
        >
          <div class="result-main">
            <h3 class="question">{{ item.question }}</h3>
            <p class="answer">{{ truncate(item.answer, 150) }}</p>
          </div>
          <div class="result-meta">
            <div class="meta-left">
              <span class="similarity-badge" :class="getSimilarityClass(item.similarity)">
                {{ (item.similarity * 100).toFixed(0) }}% 匹配
              </span>
              <span v-if="item.keywords && item.keywords.length" class="keywords">
                {{ item.keywords.slice(0, 3).join(' · ') }}
              </span>
            </div>
            <span class="view-detail">查看详情 →</span>
          </div>
        </div>
      </div>

      <div v-else-if="searched" class="empty-state">
        <div class="empty-icon">🔎</div>
        <h3>未找到相关知识</h3>
        <p>尝试使用不同的关键词搜索</p>
      </div>
      
      <div v-else class="initial-state">
        <div class="initial-icon">💡</div>
        <h3>搜索您的知识库</h3>
        <p>输入关键词查找相关知识</p>
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
            <div class="markdown-content" v-html="formatMarkdown(selectedKnowledge.answer)"></div>
          </div>
          <div v-if="selectedKnowledge.keywords && selectedKnowledge.keywords.length" class="detail-section">
            <strong>关键词：</strong>
            <div class="keyword-list">
              <span class="keyword-tag" v-for="kw in selectedKnowledge.keywords" :key="kw">
                {{ kw }}
              </span>
            </div>
          </div>
          <div class="detail-section">
            <strong>相似度：</strong>
            <span class="similarity-badge" :class="getSimilarityClass(selectedKnowledge.similarity)">
              {{ (selectedKnowledge.similarity * 100).toFixed(1) }}%
            </span>
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
import { marked } from 'marked'
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

const formatMarkdown = (text) => {
  if (!text) return ''
  return marked(text)
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getSimilarityClass = (similarity) => {
  if (similarity >= 0.8) return 'high'
  if (similarity >= 0.5) return 'medium'
  return 'low'
}
</script>

<style scoped>
.search-view {
  padding: 0;
}

.card-header {
  margin-bottom: 20px;
}

.card-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.search-input-wrapper {
  margin-bottom: 24px;
}

.search-input {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-secondary);
  padding: 8px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.search-input:focus-within {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.search-icon {
  font-size: 18px;
  padding-left: 8px;
  opacity: 0.5;
}

.search-text {
  flex: 1;
  border: none;
  background: transparent;
  padding: 8px;
}

.search-text:focus {
  box-shadow: none;
}

.search-btn {
  flex-shrink: 0;
}

.loading-state {
  padding: 20px;
}

.skeleton-item {
  height: 100px;
  margin-bottom: 16px;
}

.result-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
}

.result-count {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.results {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
  animation: fadeIn 0.3s ease;
  border: 1px solid transparent;
}

.result-item:hover {
  background: var(--bg-hover);
  border-color: var(--primary-color);
  transform: translateX(4px);
}

.result-main {
  margin-bottom: 12px;
}

.question {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.answer {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.result-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.meta-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.similarity-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--radius-xl);
}

.similarity-badge.high {
  background: rgba(82, 196, 26, 0.15);
  color: var(--success-color);
}

.similarity-badge.medium {
  background: rgba(250, 173, 20, 0.15);
  color: var(--warning-color);
}

.similarity-badge.low {
  background: rgba(255, 77, 79, 0.15);
  color: var(--danger-color);
}

.keywords {
  font-size: 12px;
  color: var(--text-muted);
}

.view-detail {
  font-size: 13px;
  color: var(--primary-color);
  font-weight: 500;
}

.empty-state,
.initial-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon,
.initial-icon {
  font-size: 56px;
  margin-bottom: 20px;
  opacity: 0.4;
}

.empty-state h3,
.initial-state h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-state p,
.initial-state p {
  font-size: 14px;
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
  backdrop-filter: blur(4px);
}

.detail-content {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  max-width: 700px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
  animation: fadeIn 0.2s ease;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px;
  border-bottom: 1px solid var(--border-light);
}

.detail-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  padding-right: 20px;
  color: var(--text-primary);
}

.close-btn {
  background: var(--bg-secondary);
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--text-secondary);
  width: 36px;
  height: 36px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.detail-body {
  padding: 24px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section strong {
  display: block;
  margin-bottom: 10px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.keyword-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-tag {
  display: inline-block;
  background: var(--primary-light);
  color: var(--primary-color);
  padding: 6px 14px;
  border-radius: var(--radius-xl);
  font-size: 13px;
  font-weight: 500;
}

@media (max-width: 768px) {
  .search-input {
    flex-wrap: wrap;
  }
  
  .search-text {
    width: 100%;
    order: 1;
  }
  
  .search-icon {
    display: none;
  }
  
  .search-btn {
    width: 100%;
    order: 2;
  }
  
  .btn-text {
    display: inline;
  }
  
  .btn-icon {
    display: none;
  }
  
  .view-detail {
    display: none;
  }
}
</style>

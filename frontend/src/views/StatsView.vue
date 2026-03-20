<template>
  <div class="stats-view">
    <div class="card">
      <div class="card-header">
        <h2>📊 知识库统计</h2>
        <button class="btn btn-secondary" @click="loadStats">
          🔄 刷新
        </button>
      </div>

      <div v-if="loading" class="loading"></div>

      <div v-else class="stats-content">
        <div class="stat-cards">
          <div class="stat-card primary">
            <div class="stat-icon">📚</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_knowledge }}</div>
              <div class="stat-label">总知识条目</div>
            </div>
          </div>
          <div class="stat-card success">
            <div class="stat-icon">📁</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.catalogs_count }}</div>
              <div class="stat-label">知识目录数</div>
            </div>
          </div>
          <div class="stat-card warning">
            <div class="stat-icon">📅</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.today_count }}</div>
              <div class="stat-label">今日新增</div>
            </div>
          </div>
          <div class="stat-card info">
            <div class="stat-icon">📆</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.week_count }}</div>
              <div class="stat-label">本周新增</div>
            </div>
          </div>
        </div>

        <div class="stats-grid">
          <div class="stats-section">
            <h3>🕐 最近添加</h3>
            <div class="latest-list">
              <div 
                v-for="item in stats.latest_knowledge" 
                :key="item.id" 
                class="latest-item"
              >
                <span class="latest-question">{{ item.question }}</span>
                <span class="latest-time">{{ formatDate(item.created_at) }}</span>
              </div>
              <div v-if="!stats.latest_knowledge || stats.latest_knowledge.length === 0" class="empty-list">
                暂无知识记录
              </div>
            </div>
          </div>

          <div class="stats-section">
            <h3>📊 目录分布</h3>
            <div class="distribution-list">
              <div 
                v-for="item in stats.catalog_distribution" 
                :key="item.catalog_id" 
                class="distribution-item"
              >
                <div class="distribution-info">
                  <span class="distribution-name">📁 {{ item.catalog_name }}</span>
                  <span class="distribution-count">{{ item.count }} 条</span>
                </div>
                <div class="distribution-bar">
                  <div 
                    class="distribution-fill" 
                    :style="{ width: getBarWidth(item.count) }"
                  ></div>
                </div>
              </div>
              <div v-if="!stats.catalog_distribution || stats.catalog_distribution.length === 0" class="empty-list">
                暂无目录数据
              </div>
            </div>
          </div>

          <div class="stats-section full-width">
            <h3>🏷️ 热门关键词</h3>
            <div class="keywords-cloud">
              <span 
                v-for="item in stats.top_keywords" 
                :key="item.keyword" 
                class="keyword-tag"
                :style="{ fontSize: getKeywordSize(item.count) }"
              >
                {{ item.keyword }} ({{ item.count }})
              </span>
              <div v-if="!stats.top_keywords || stats.top_keywords.length === 0" class="empty-list">
                暂无关键词数据
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { knowledgeApi } from '../api'

const stats = ref({
  total_knowledge: 0,
  catalogs_count: 0,
  today_count: 0,
  week_count: 0,
  month_count: 0,
  latest_knowledge: [],
  catalog_distribution: [],
  top_keywords: []
})
const loading = ref(false)

const loadStats = async () => {
  loading.value = true
  try {
    const response = await knowledgeApi.getStatistics()
    stats.value = response.data
  } catch (error) {
    console.error('Failed to load statistics:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

const getBarWidth = (count) => {
  const max = Math.max(...stats.value.catalog_distribution.map(c => c.count), 1)
  return `${(count / max) * 100}%`
}

const getKeywordSize = (count) => {
  const max = Math.max(...stats.value.top_keywords.map(k => k.count), 1)
  const size = 12 + (count / max) * 8
  return `${size}px`
}

onMounted(loadStats)
</script>

<style scoped>
.stats-view {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 12px;
  color: white;
}

.stat-card.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card.success {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.stat-card.warning {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card.info {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon {
  font-size: 32px;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  opacity: 0.9;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.stats-section {
  background: var(--bg-color);
  border-radius: 12px;
  padding: 20px;
}

.stats-section.full-width {
  grid-column: 1 / -1;
}

.stats-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-color);
}

.latest-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.latest-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--card-bg);
  border-radius: 8px;
  transition: transform 0.2s;
}

.latest-item:hover {
  transform: translateX(4px);
}

.latest-question {
  flex: 1;
  font-size: 14px;
  color: var(--text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.latest-time {
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: 12px;
  white-space: nowrap;
}

.distribution-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.distribution-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.distribution-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.distribution-name {
  font-size: 14px;
  color: var(--text-color);
}

.distribution-count {
  font-size: 12px;
  color: var(--text-secondary);
}

.distribution-bar {
  height: 8px;
  background: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
}

.distribution-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-color), var(--primary-dark));
  border-radius: 4px;
  transition: width 0.3s ease;
}

.keywords-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.keyword-tag {
  display: inline-block;
  background: var(--primary-light);
  color: var(--primary-color);
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 500;
  transition: all 0.2s;
}

.keyword-tag:hover {
  background: var(--primary-color);
  color: white;
  transform: scale(1.05);
}

.empty-list {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary);
  font-size: 14px;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

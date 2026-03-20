<template>
  <div class="stats-view">
    <div class="card">
      <div class="card-header">
        <h2>📊 知识库统计</h2>
        <button class="btn btn-secondary" @click="loadStats">
          <span class="btn-icon">🔄</span>
          <span class="btn-text">刷新</span>
        </button>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="skeleton-grid">
          <div class="skeleton skeleton-card"></div>
          <div class="skeleton skeleton-card"></div>
          <div class="skeleton skeleton-card"></div>
          <div class="skeleton skeleton-card"></div>
        </div>
      </div>

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
                {{ item.keyword }} <span class="keyword-count">{{ item.count }}</span>
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
  const size = 13 + (count / max) * 6
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
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
}

.card-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.loading-state {
  padding: 20px;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.skeleton-card {
  height: 100px;
  border-radius: var(--radius-lg);
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: var(--radius-lg);
  color: white;
  transition: all var(--transition-fast);
  cursor: default;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.stat-card.primary {
  background: linear-gradient(135deg, #52C41A 0%, #389E0D 100%);
}

.stat-card.success {
  background: linear-gradient(135deg, #13C2C2 0%, #08979C 100%);
}

.stat-card.warning {
  background: linear-gradient(135deg, #FAAD14 0%, #D48806 100%);
}

.stat-card.info {
  background: linear-gradient(135deg, #73D13D 0%, #52C41A 100%);
}

.stat-icon {
  font-size: 32px;
  margin-right: 16px;
  opacity: 0.9;
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
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: 20px;
}

.stats-section.full-width {
  grid-column: 1 / -1;
}

.stats-section h3 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-primary);
}

.latest-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.latest-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.latest-item:hover {
  transform: translateX(4px);
  box-shadow: var(--shadow-sm);
}

.latest-question {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.latest-time {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: 12px;
  white-space: nowrap;
}

.distribution-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
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
  color: var(--text-primary);
}

.distribution-count {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.distribution-bar {
  height: 8px;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.distribution-fill {
  height: 100%;
  background: var(--primary-gradient);
  border-radius: var(--radius-xl);
  transition: width 0.5s ease;
}

.keywords-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.keyword-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-card);
  color: var(--primary-color);
  padding: 8px 14px;
  border-radius: var(--radius-xl);
  font-weight: 500;
  transition: all var(--transition-fast);
  border: 1px solid var(--border-color);
}

.keyword-tag:hover {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
  transform: scale(1.05);
}

.keyword-count {
  font-size: 0.85em;
  opacity: 0.7;
}

.empty-list {
  text-align: center;
  padding: 24px;
  color: var(--text-muted);
  font-size: 14px;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .skeleton-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .btn-text {
    display: none;
  }
}
</style>

<template>
  <div class="discovery-view">
    <div class="card">
      <div class="card-header">
        <h2>🌟 每日发现</h2>
        <div class="header-actions">
          <button class="btn btn-secondary" @click="refreshAll" :disabled="loading">
            <span class="btn-icon">🔄</span>
            <span class="btn-text">刷新</span>
          </button>
        </div>
      </div>

      <div class="tabs">
        <div 
          class="tab" 
          :class="{ active: activeTab === 'hotspots' }"
          @click="activeTab = 'hotspots'"
        >
          🔥 每日热点
        </div>
        <div 
          class="tab" 
          :class="{ active: activeTab === 'recommendations' }"
          @click="activeTab = 'recommendations'"
        >
          📚 学习推荐
        </div>
        <div 
          class="tab" 
          :class="{ active: activeTab === 'gaps' }"
          @click="activeTab = 'gaps'"
        >
          🎯 知识盲区
        </div>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <span>加载中...</span>
      </div>

      <div v-else>
        <div v-if="activeTab === 'hotspots'" class="hotspots-tab">
          <div class="hotspots-header">
            <h3>🔥 与您知识相关的热点内容</h3>
            <p class="hotspots-desc">基于您的知识领域，为您推荐最新的技术动态和行业资讯</p>
          </div>

          <div v-if="hotspots.length === 0" class="empty-state">
            <div class="empty-icon">📭</div>
            <p>暂无热点内容</p>
            <p class="empty-hint">配置 TAVILY_API_KEY 后可获取网络热点</p>
          </div>

          <div v-else class="hotspots-list">
            <div 
              v-for="(item, index) in hotspots" 
              :key="index" 
              class="hotspot-card"
            >
              <div class="hotspot-header">
                <span class="hotspot-category">{{ item.category }}</span>
                <span class="hotspot-time">{{ formatTime(item.fetched_at) }}</span>
              </div>
              <h4 class="hotspot-title">{{ item.title }}</h4>
              <p class="hotspot-summary">{{ item.summary }}</p>
              <div v-if="item.url" class="hotspot-footer">
                <a :href="item.url" target="_blank" class="hotspot-link">
                  查看原文 →
                </a>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'recommendations'" class="recommendations-tab">
          <div class="recommendation-section">
            <h3>📖 下一步学习</h3>
            <div v-if="recommendations.next_topics?.length === 0" class="empty-state">
              暂无推荐
            </div>
            <div v-else class="recommendation-list">
              <div 
                v-for="(topic, index) in recommendations.next_topics" 
                :key="index" 
                class="recommendation-card"
                :class="topic.priority"
              >
                <div class="recommendation-priority">{{ getPriorityLabel(topic.priority) }}</div>
                <h4 class="recommendation-title">{{ topic.topic }}</h4>
                <p class="recommendation-reason">{{ topic.reason }}</p>
              </div>
            </div>
          </div>

          <div class="recommendation-section">
            <h3>🧭 拓展方向</h3>
            <div v-if="recommendations.expand_directions?.length === 0" class="empty-state">
              暂无拓展建议
            </div>
            <div v-else class="direction-list">
              <div 
                v-for="(direction, index) in recommendations.expand_directions" 
                :key="index" 
                class="direction-card"
              >
                <h4 class="direction-title">{{ direction.direction }}</h4>
                <p class="direction-description">{{ direction.description }}</p>
                <div v-if="direction.related_topics?.length > 0" class="related-topics">
                  <span class="related-label">相关知识点:</span>
                  <span 
                    v-for="topic in direction.related_topics" 
                    :key="topic" 
                    class="related-tag"
                  >
                    {{ topic }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div class="recommendation-section">
            <h3>🔬 深入学习</h3>
            <div v-if="recommendations.deep_dive_areas?.length === 0" class="empty-state">
              暂无深入建议
            </div>
            <div v-else class="deep-dive-list">
              <div 
                v-for="(area, index) in recommendations.deep_dive_areas" 
                :key="index" 
                class="deep-dive-card"
              >
                <h4 class="deep-dive-title">{{ area.area }}</h4>
                <div class="deep-dive-levels">
                  <div class="level-item">
                    <span class="level-label">当前水平:</span>
                    <span class="level-value">{{ area.current_level }}</span>
                  </div>
                  <div class="level-item">
                    <span class="level-label">建议深度:</span>
                    <span class="level-value highlight">{{ area.suggested_depth }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'gaps'" class="gaps-tab">
          <div class="gaps-summary">
            <div class="gap-stat">
              <div class="stat-value">{{ gaps.total_domains }}</div>
              <div class="stat-label">知识领域</div>
            </div>
            <div class="gap-stat">
              <div class="stat-value">{{ gaps.total_knowledge }}</div>
              <div class="stat-label">知识条目</div>
            </div>
            <div class="gap-stat warning">
              <div class="stat-value">{{ gaps.identified_gaps?.length || 0 }}</div>
              <div class="stat-label">知识盲区</div>
            </div>
          </div>

          <div class="gaps-distribution">
            <h3>📊 知识分布</h3>
            <div class="distribution-chart">
              <div 
                v-for="(count, domain) in gaps.domain_distribution" 
                :key="domain" 
                class="distribution-bar-item"
              >
                <div class="bar-label">{{ domain }}</div>
                <div class="bar-container">
                  <div 
                    class="bar-fill" 
                    :style="{ width: getBarWidth(count) }"
                  ></div>
                </div>
                <div class="bar-count">{{ count }}</div>
              </div>
            </div>
          </div>

          <div v-if="gaps.identified_gaps?.length > 0" class="gaps-list">
            <h3>⚠️ 需要补充的知识领域</h3>
            <div class="gap-items">
              <div 
                v-for="(gap, index) in gaps.identified_gaps" 
                :key="index" 
                class="gap-item"
              >
                <div class="gap-domain">{{ gap.domain }}</div>
                <div class="gap-info">
                  <span>当前: {{ gap.current_count }} 条</span>
                  <span>建议: {{ gap.suggested_min }} 条</span>
                </div>
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
import { discoveryApi } from '../api'

const activeTab = ref('hotspots')
const loading = ref(false)
const hotspots = ref([])
const recommendations = ref({
  next_topics: [],
  expand_directions: [],
  deep_dive_areas: []
})
const gaps = ref({
  total_domains: 0,
  total_knowledge: 0,
  domain_distribution: {},
  identified_gaps: []
})

const summary = ref(null)

const loadHotspots = async () => {
  try {
    const response = await discoveryApi.getHotspots()
    hotspots.value = response.data
  } catch (error) {
    console.error('Failed to load hotspots:', error)
  }
}

const loadRecommendations = async () => {
  try {
    const response = await discoveryApi.getRecommendations()
    recommendations.value = response.data
  } catch (error) {
    console.error('Failed to load recommendations:', error)
  }
}

const loadGaps = async () => {
  try {
    const response = await discoveryApi.getGaps()
    gaps.value = response.data
  } catch (error) {
    console.error('Failed to load gaps:', error)
  }
}

const loadSummary = async () => {
  try {
    const response = await discoveryApi.getSummary()
    summary.value = response.data
  } catch (error) {
    console.error('Failed to load summary:', error)
  }
}

const refreshAll = async () => {
  loading.value = true
  try {
    await discoveryApi.refreshCache()
    await Promise.all([
      loadHotspots(),
      loadRecommendations(),
      loadGaps(),
      loadSummary()
    ])
  } catch (error) {
    console.error('Failed to refresh:', error)
  } finally {
    loading.value = false
  }
}

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getPriorityLabel = (priority) => {
  const labels = {
    high: '🔴 高优先',
    medium: '🟡 中优先',
    low: '🟢 低优先'
  }
  return labels[priority] || priority
}

const getBarWidth = (count) => {
  const max = Math.max(...Object.values(gaps.value.domain_distribution), 1)
  return `${(count / max) * 100}%`
}

onMounted(() => {
  loadSummary()
  loadHotspots()
  loadRecommendations()
  loadGaps()
})
</script>

<style scoped>
.discovery-view {
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

.header-actions {
  display: flex;
  gap: 12px;
}

.btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
}

.tab {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.tab.active {
  background: var(--primary-color);
  color: white;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: var(--text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-light);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 8px;
}

.hotspots-header {
  margin-bottom: 24px;
}

.hotspots-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.hotspots-desc {
  font-size: 14px;
  color: var(--text-secondary);
}

.hotspots-list {
  display: grid;
  gap: 16px;
}

.hotspot-card {
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  transition: all var(--transition-fast);
}

.hotspot-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.hotspot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.hotspot-category {
  font-size: 12px;
  padding: 4px 12px;
  background: var(--primary-light);
  color: var(--primary-color);
  border-radius: var(--radius-md);
}

.hotspot-time {
  font-size: 12px;
  color: var(--text-tertiary);
}

.hotspot-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.hotspot-summary {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.hotspot-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-light);
}

.hotspot-link {
  font-size: 13px;
  color: var(--primary-color);
  text-decoration: none;
}

.hotspot-link:hover {
  text-decoration: underline;
}

.recommendation-section {
  margin-bottom: 32px;
}

.recommendation-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.recommendation-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.recommendation-card {
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border-left: 4px solid var(--border-light);
}

.recommendation-card.high {
  border-left-color: #ff4d4f;
}

.recommendation-card.medium {
  border-left-color: #faad14;
}

.recommendation-card.low {
  border-left-color: #52c41a;
}

.recommendation-priority {
  font-size: 12px;
  margin-bottom: 8px;
}

.recommendation-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.recommendation-reason {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.direction-list,
.deep-dive-list {
  display: grid;
  gap: 16px;
}

.direction-card,
.deep-dive-card {
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.direction-title,
.deep-dive-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.direction-description {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 12px;
}

.related-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.related-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.related-tag {
  font-size: 12px;
  padding: 4px 10px;
  background: var(--bg-hover);
  color: var(--text-secondary);
  border-radius: var(--radius-md);
}

.deep-dive-levels {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.level-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.level-label {
  color: var(--text-tertiary);
}

.level-value {
  color: var(--text-secondary);
}

.level-value.highlight {
  color: var(--primary-color);
  font-weight: 500;
}

.gaps-summary {
  display: flex;
  gap: 24px;
  margin-bottom: 32px;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.gap-stat {
  text-align: center;
  flex: 1;
}

.gap-stat .stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
}

.gap-stat.warning .stat-value {
  color: #faad14;
}

.gap-stat .stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.gaps-distribution {
  margin-bottom: 32px;
}

.gaps-distribution h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.distribution-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.distribution-bar-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bar-label {
  width: 120px;
  font-size: 13px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-container {
  flex: 1;
  height: 24px;
  background: var(--bg-hover);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-color), var(--primary-light));
  border-radius: var(--radius-md);
  transition: width 0.3s ease;
}

.bar-count {
  width: 40px;
  text-align: right;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.gaps-list h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.gap-items {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 12px;
}

.gap-item {
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border-left: 3px solid #faad14;
}

.gap-domain {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.gap-info {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .gaps-summary {
    flex-direction: column;
    gap: 16px;
  }
  
  .recommendation-list {
    grid-template-columns: 1fr;
  }
  
  .distribution-bar-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .bar-label {
    width: auto;
  }
  
  .bar-container {
    width: 100%;
  }
  
  .bar-count {
    width: auto;
    text-align: left;
  }
}
</style>

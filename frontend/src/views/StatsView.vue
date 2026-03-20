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
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_knowledge }}</div>
            <div class="stat-label">总知识条目</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.catalogs_count }}</div>
            <div class="stat-label">知识目录数</div>
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
  catalogs_count: 0
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
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  padding: 24px;
  border-radius: 12px;
  text-align: center;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}
</style>

<template>
  <div class="catalog-view">
    <div class="card">
      <div class="card-header">
        <div class="header-left">
          <h2>📚 知识目录</h2>
          <span class="knowledge-count" v-if="tree">
            {{ totalKnowledge }} 条知识
          </span>
        </div>
        <button class="btn btn-secondary" @click="loadTree">
          <span class="btn-icon">🔄</span>
          <span class="btn-text">刷新</span>
        </button>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="skeleton skeleton-title"></div>
        <div class="skeleton skeleton-item"></div>
        <div class="skeleton skeleton-item"></div>
        <div class="skeleton skeleton-item"></div>
      </div>

      <div v-else-if="!tree" class="empty-state">
        <div class="empty-icon">📭</div>
        <h3>知识目录为空</h3>
        <p>开始提问来建立您的知识体系吧！</p>
      </div>

      <div v-else class="tree-container">
        <TreeNode :node="tree" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { catalogApi } from '../api'
import TreeNode from '../components/TreeNode.vue'

const tree = ref(null)
const loading = ref(false)

const totalKnowledge = computed(() => {
  if (!tree.value) return 0
  const count = (node) => {
    let total = node.knowledge_count || 0
    if (node.children) {
      node.children.forEach(child => {
        total += count(child)
      })
    }
    return total
  }
  return count(tree.value)
})

const loadTree = async () => {
  loading.value = true
  try {
    const response = await catalogApi.getTree()
    tree.value = response.data
  } catch (error) {
    console.error('Failed to load catalog tree:', error)
  } finally {
    loading.value = false
  }
}

onMounted(loadTree)
</script>

<style scoped>
.catalog-view {
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

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.knowledge-count {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 4px 12px;
  border-radius: var(--radius-xl);
}

.btn-icon {
  font-size: 14px;
}

.loading-state {
  padding: 20px;
}

.skeleton-title {
  height: 24px;
  width: 200px;
  margin-bottom: 24px;
}

.skeleton-item {
  height: 48px;
  width: 100%;
  margin-bottom: 12px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 56px;
  margin-bottom: 20px;
  opacity: 0.4;
}

.empty-state h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 14px;
  color: var(--text-secondary);
}

.tree-container {
  padding: 8px 0;
}

@media (max-width: 768px) {
  .btn-text {
    display: none;
  }
  
  .knowledge-count {
    display: none;
  }
}
</style>

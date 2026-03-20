<template>
  <div class="catalog-view">
    <div class="card">
      <div class="card-header">
        <h2>📚 知识目录</h2>
        <button class="btn btn-secondary" @click="loadTree">
          🔄 刷新
        </button>
      </div>

      <div v-if="loading" class="loading"></div>

      <div v-else-if="!tree" class="empty">
        知识目录为空，开始提问来建立您的知识体系吧！
      </div>

      <div v-else class="tree">
        <TreeNode :node="tree" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { catalogApi } from '../api'
import TreeNode from '../components/TreeNode.vue'

const tree = ref(null)
const loading = ref(false)

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
  margin-bottom: 20px;
}

.card-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.empty {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.tree {
  padding: 10px 0;
}
</style>

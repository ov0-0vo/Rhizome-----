<template>
  <div class="tree-node">
    <div class="node-content" @click="toggleNode">
      <span class="expand-icon">{{ expandIcon }}</span>
      <span class="node-name">{{ node.name }}</span>
      <span class="knowledge-count" v-if="node.knowledge_count > 0">
        {{ node.knowledge_count }}
      </span>
    </div>
    
    <transition name="slide">
      <div v-if="showChildren" class="children">
        <TreeNode 
          v-for="child in node.children" 
          :key="child.id" 
          :node="child"
        />
      </div>
    </transition>

    <transition name="slide">
      <div v-if="showKnowledgeList" class="knowledge-list">
        <div 
          v-for="item in knowledgeList" 
          :key="item.id" 
          class="knowledge-item"
          @click="selectedKnowledge = item"
        >
          <div class="knowledge-question">{{ item.question }}</div>
          <div class="knowledge-meta">
            <span v-if="item.keywords && item.keywords.length" class="keywords">
              {{ item.keywords.slice(0, 2).join(' · ') }}
            </span>
          </div>
        </div>
      </div>
    </transition>

    <div v-if="loadingKnowledge" class="loading-knowledge">
      <div class="loading-dots">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
    </div>

    <div v-if="showKnowledge && !loadingKnowledge && knowledgeList.length === 0 && node.knowledge_count > 0" class="no-knowledge">
      暂无知识数据
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
            <strong>创建时间：</strong>
            {{ formatDate(selectedKnowledge.created_at) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { marked } from 'marked'
import { knowledgeApi } from '../api'

const props = defineProps({
  node: {
    type: Object,
    required: true
  }
})

const expanded = ref(false)
const showKnowledge = ref(false)
const knowledgeList = ref([])
const loadingKnowledge = ref(false)
const selectedKnowledge = ref(null)

const hasChildren = computed(() => {
  return props.node.children && props.node.children.length > 0
})

const expandIcon = computed(() => {
  if (hasChildren.value) {
    return expanded.value ? '📂' : '📁'
  }
  return showKnowledge.value ? '📖' : '📄'
})

const showChildren = computed(() => {
  return hasChildren.value && expanded.value
})

const showKnowledgeList = computed(() => {
  return showKnowledge.value && knowledgeList.value.length > 0
})

const formatMarkdown = (text) => {
  if (!text) return ''
  return marked(text)
}

const toggleNode = async () => {
  if (hasChildren.value) {
    expanded.value = !expanded.value
  }
  
  showKnowledge.value = !showKnowledge.value
  
  if (showKnowledge.value && knowledgeList.value.length === 0) {
    await loadKnowledge()
  }
}

const loadKnowledge = async () => {
  if (props.node.knowledge_count === 0) {
    return
  }
  
  loadingKnowledge.value = true
  try {
    const response = await knowledgeApi.getByCatalog(props.node.id)
    knowledgeList.value = response.data || []
  } catch (error) {
    console.error('Failed to load knowledge:', error)
    knowledgeList.value = []
  } finally {
    loadingKnowledge.value = false
  }
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.tree-node {
  margin-left: 20px;
}

.tree-node:first-child {
  margin-left: 0;
}

.node-content {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  user-select: none;
}

.node-content:hover {
  background: var(--bg-secondary);
}

.expand-icon {
  margin-right: 10px;
  font-size: 18px;
  transition: transform var(--transition-fast);
}

.node-name {
  font-weight: 500;
  font-size: 14px;
  color: var(--text-primary);
}

.knowledge-count {
  margin-left: auto;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 2px 8px;
  border-radius: var(--radius-xl);
}

.children {
  border-left: 2px solid var(--border-color);
  margin-left: 18px;
  padding-left: 8px;
  margin-top: 4px;
}

.knowledge-list {
  margin-left: 28px;
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.knowledge-item {
  padding: 12px 14px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.knowledge-item:hover {
  background: var(--bg-hover);
  transform: translateX(4px);
}

.knowledge-question {
  font-weight: 500;
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.knowledge-meta {
  font-size: 12px;
  color: var(--text-muted);
}

.keywords {
  color: var(--primary-color);
}

.loading-knowledge {
  margin-left: 28px;
  padding: 12px;
}

.loading-dots {
  display: flex;
  gap: 6px;
}

.loading-dots .dot {
  width: 8px;
  height: 8px;
  background: var(--text-muted);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots .dot:nth-child(1) { animation-delay: -0.32s; }
.loading-dots .dot:nth-child(2) { animation-delay: -0.16s; }

.no-knowledge {
  margin-left: 28px;
  padding: 12px;
  color: var(--text-muted);
  font-size: 13px;
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

.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 768px) {
  .tree-node {
    margin-left: 12px;
  }
  
  .children {
    margin-left: 12px;
  }
  
  .knowledge-list {
    margin-left: 18px;
  }
}
</style>

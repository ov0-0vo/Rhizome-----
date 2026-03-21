<template>
  <div class="tree-node" :class="{ 'root-node': isRoot }">
    <div class="node-content" @click="toggleNode">
      <span class="expand-icon">{{ expandIcon }}</span>
      <span class="node-name">{{ node.name }}</span>
      <span class="knowledge-count" v-if="node.knowledge_count > 0">
        {{ node.knowledge_count }}
      </span>
      <div class="node-actions" @click.stop>
        <button class="action-btn" title="新建子目录" @click="emitCreateSubCatalog">
          <span>➕</span>
        </button>
        <button class="action-btn" title="编辑目录" @click="emitEditCatalog">
          <span>✏️</span>
        </button>
        <button class="action-btn delete" title="删除目录" @click="emitDeleteCatalog">
          <span>🗑️</span>
        </button>
      </div>
    </div>
    
    <transition name="slide">
      <div v-if="showChildren" class="children">
        <TreeNode 
          v-for="child in node.children" 
          :key="child.id" 
          :node="child"
          @create-sub-catalog="$emit('create-sub-catalog', $event)"
          @edit-catalog="$emit('edit-catalog', $event)"
          @delete-catalog="$emit('delete-catalog', $event)"
          @refresh="$emit('refresh')"
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
  },
  isRoot: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['create-sub-catalog', 'edit-catalog', 'delete-catalog', 'refresh'])

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

const emitCreateSubCatalog = () => {
  emit('create-sub-catalog', {
    parentId: props.node.id,
    parentName: props.node.name
  })
}

const emitEditCatalog = () => {
  emit('edit-catalog', {
    catalogId: props.node.id,
    name: props.node.name,
    keywords: props.node.keywords
  })
}

const emitDeleteCatalog = () => {
  emit('delete-catalog', {
    catalogId: props.node.id,
    catalogName: props.node.name
  })
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.tree-node {
  margin-left: 20px;
}

.tree-node.root-node {
  margin-left: 0;
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

.node-content:hover .node-actions {
  opacity: 1;
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
  flex: 1;
}

.knowledge-count {
  margin-left: 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 2px 8px;
  border-radius: var(--radius-xl);
}

.node-actions {
  display: flex;
  gap: 4px;
  margin-left: 12px;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.action-btn {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--bg-card);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.action-btn span {
  font-size: 12px;
}

.action-btn:hover {
  background: var(--bg-hover);
  transform: scale(1.1);
}

.action-btn.delete:hover {
  background: #fee2e2;
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

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

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

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
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

.markdown-content {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  margin-top: 16px;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.markdown-content :deep(p) {
  margin-bottom: 12px;
}

.markdown-content :deep(code) {
  background: var(--bg-secondary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: monospace;
}

.markdown-content :deep(pre) {
  background: var(--bg-secondary);
  padding: 12px;
  border-radius: var(--radius-md);
  overflow-x: auto;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 20px;
  margin-bottom: 12px;
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
  
  .node-actions {
    opacity: 1;
  }
}
</style>

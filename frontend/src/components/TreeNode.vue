<template>
  <div class="tree-node">
    <div class="node-content" @click="toggleNode">
      <span class="expand-icon">{{ expandIcon }}</span>
      <span class="node-name">{{ node.name }}</span>
      <span class="knowledge-count">({{ node.knowledge_count }} 条知识)</span>
    </div>
    
    <div v-if="showChildren" class="children">
      <TreeNode 
        v-for="child in node.children" 
        :key="child.id" 
        :node="child"
      />
    </div>

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
            {{ item.keywords.slice(0, 3).join(', ') }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="loadingKnowledge" class="loading-knowledge">
      加载中...
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
            <span class="keyword-tag" v-for="kw in selectedKnowledge.keywords" :key="kw">
              {{ kw }}
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
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.node-content:hover {
  background-color: var(--bg-color);
}

.expand-icon {
  margin-right: 8px;
  font-size: 16px;
}

.node-name {
  font-weight: 500;
}

.knowledge-count {
  margin-left: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.children {
  border-left: 2px solid var(--border-color);
  margin-left: 12px;
  padding-left: 8px;
}

.knowledge-list {
  margin-left: 28px;
  margin-top: 8px;
}

.knowledge-item {
  padding: 10px 12px;
  margin-bottom: 6px;
  background: var(--bg-color);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.knowledge-item:hover {
  background: var(--primary-light);
  transform: translateX(4px);
}

.knowledge-question {
  font-weight: 500;
  margin-bottom: 4px;
}

.knowledge-meta {
  font-size: 12px;
  color: var(--text-secondary);
}

.keywords {
  color: var(--primary-color);
}

.loading-knowledge,
.no-knowledge {
  margin-left: 28px;
  padding: 10px;
  color: var(--text-secondary);
  font-style: italic;
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
  max-width: 700px;
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

.markdown-content {
  line-height: 1.8;
  color: var(--text-color);
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  margin-top: 1em;
  margin-bottom: 0.5em;
  color: var(--text-color);
}

.markdown-content :deep(p) {
  margin-bottom: 1em;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 2em;
  margin-bottom: 1em;
}

.markdown-content :deep(li) {
  margin-bottom: 0.5em;
}

.markdown-content :deep(code) {
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  background-color: #f8f8f8;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin-bottom: 1em;
  border: 1px solid var(--border-color);
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid var(--primary-color);
  padding-left: 16px;
  margin: 1em 0;
  color: var(--text-secondary);
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1em;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid var(--border-color);
  padding: 8px 12px;
  text-align: left;
}

.markdown-content :deep(th) {
  background-color: var(--bg-color);
  font-weight: 600;
}

.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 1.5em 0;
}

.markdown-content :deep(strong) {
  font-weight: 600;
}

.markdown-content :deep(em) {
  font-style: italic;
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

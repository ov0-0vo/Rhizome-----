<template>
  <div class="documents-view">
    <div class="card">
      <div class="card-header">
        <div class="header-left">
          <h2>📄 导入文档管理</h2>
          <span class="doc-count" v-if="stats">
            {{ stats.total_documents }} 个文档 / {{ stats.total_knowledge }} 条知识
          </span>
        </div>
        <div class="header-actions">
          <button class="btn btn-secondary" @click="loadDocuments">
            <span class="btn-icon">🔄</span>
            <span class="btn-text">刷新</span>
          </button>
        </div>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="skeleton skeleton-title"></div>
        <div class="skeleton skeleton-item"></div>
        <div class="skeleton skeleton-item"></div>
      </div>

      <div v-else-if="documents.length === 0" class="empty-state">
        <div class="empty-icon">📭</div>
        <h3>暂无导入文档</h3>
        <p>导入 Markdown 文件后，原文档将保存在这里</p>
      </div>

      <div v-else class="documents-list">
        <div 
          v-for="doc in documents" 
          :key="doc.id" 
          class="document-item"
          @click="viewDocument(doc)"
        >
          <div class="doc-icon">📄</div>
          <div class="doc-info">
            <div class="doc-name">{{ doc.filename }}</div>
            <div class="doc-meta">
              <span class="meta-item">
                <span class="meta-icon">📅</span>
                {{ formatDate(doc.imported_at) }}
              </span>
              <span class="meta-item">
                <span class="meta-icon">📊</span>
                {{ doc.imported_count }} 条知识
              </span>
              <span class="meta-item">
                <span class="meta-icon">📦</span>
                {{ formatSize(doc.file_size) }}
              </span>
            </div>
          </div>
          <div class="doc-actions">
            <button class="btn-icon-only" @click.stop="viewDocument(doc)" title="查看原文">
              👁️
            </button>
            <button class="btn-icon-only danger" @click.stop="confirmDelete(doc)" title="删除">
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showViewer" class="modal-overlay" @click="closeViewer">
      <div class="modal-content document-viewer" @click.stop>
        <div class="modal-header">
          <h3>📄 {{ currentDoc?.filename }}</h3>
          <button class="btn-close" @click="closeViewer">×</button>
        </div>
        <div class="modal-body">
          <div v-if="loadingContent" class="loading-state">
            <div class="loading-dots">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
            <p>加载中...</p>
          </div>
          <div v-else class="markdown-content" v-html="renderedContent"></div>
        </div>
        <div class="modal-footer">
          <div class="doc-stats">
            <span>导入时间: {{ formatDate(currentDoc?.imported_at) }}</span>
            <span>知识条目: {{ currentDoc?.imported_count }}</span>
          </div>
          <button class="btn btn-secondary" @click="closeViewer">关闭</button>
        </div>
      </div>
    </div>

    <div v-if="showDeleteConfirm" class="modal-overlay" @click="showDeleteConfirm = false">
      <div class="modal-content delete-confirm" @click.stop>
        <div class="modal-header">
          <h3>⚠️ 确认删除</h3>
        </div>
        <div class="modal-body">
          <p>确定要删除文档 <strong>{{ docToDelete?.filename }}</strong> 吗？</p>
          <p class="warning-text">注意：这只会删除原文档记录，已导入的知识条目不会被删除。</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDeleteConfirm = false">取消</button>
          <button class="btn btn-danger" @click="deleteDocument">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { importApi } from '../api'

const documents = ref([])
const stats = ref(null)
const loading = ref(true)
const showViewer = ref(false)
const showDeleteConfirm = ref(false)
const currentDoc = ref(null)
const docToDelete = ref(null)
const loadingContent = ref(false)
const rawContent = ref('')

const renderedContent = computed(() => {
  if (!rawContent.value) return ''
  return renderMarkdown(rawContent.value)
})

function renderMarkdown(text) {
  let html = text
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
    .replace(/^\- (.*$)/gim, '<li>$1</li>')
    .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
  
  html = '<p>' + html + '</p>'
  html = html.replace(/<p><\/p>/g, '')
  html = html.replace(/<p>(<h[1-6]>)/g, '$1')
  html = html.replace(/(<\/h[1-6]>)<\/p>/g, '$1')
  html = html.replace(/<p>(<pre>)/g, '$1')
  html = html.replace(/(<\/pre>)<\/p>/g, '$1')
  
  return html
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function loadDocuments() {
  loading.value = true
  try {
    const [docsRes, statsRes] = await Promise.all([
      importApi.getDocuments(),
      importApi.getDocumentStats()
    ])
    documents.value = docsRes.data
    stats.value = statsRes.data
  } catch (e) {
    console.error('Failed to load documents:', e)
  } finally {
    loading.value = false
  }
}

async function viewDocument(doc) {
  currentDoc.value = doc
  showViewer.value = true
  loadingContent.value = true
  rawContent.value = ''
  
  try {
    const res = await importApi.getDocument(doc.id)
    rawContent.value = res.data.content || ''
    currentDoc.value = res.data
  } catch (e) {
    console.error('Failed to load document content:', e)
    rawContent.value = '加载失败'
  } finally {
    loadingContent.value = false
  }
}

function closeViewer() {
  showViewer.value = false
  currentDoc.value = null
  rawContent.value = ''
}

function confirmDelete(doc) {
  docToDelete.value = doc
  showDeleteConfirm.value = true
}

async function deleteDocument() {
  if (!docToDelete.value) return
  
  try {
    await importApi.deleteDocument(docToDelete.value.id)
    documents.value = documents.value.filter(d => d.id !== docToDelete.value.id)
    if (stats.value) {
      stats.value.total_documents -= 1
      stats.value.total_knowledge -= docToDelete.value.imported_count
      stats.value.total_size -= docToDelete.value.file_size
    }
    showDeleteConfirm.value = false
    docToDelete.value = null
  } catch (e) {
    console.error('Failed to delete document:', e)
    alert('删除失败')
  }
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.documents-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.card {
  background: var(--card-bg, #fff);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border-color, #eee);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 1.5rem;
}

.doc-count {
  font-size: 0.875rem;
  color: var(--text-secondary, #666);
  background: var(--bg-secondary, #f5f5f5);
  padding: 4px 12px;
  border-radius: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--primary-color, #4a90d9);
  color: white;
}

.btn-secondary {
  background: var(--bg-secondary, #f5f5f5);
  color: var(--text-primary, #333);
}

.btn-danger {
  background: #e74c3c;
  color: white;
}

.btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.loading-state {
  padding: 40px;
  text-align: center;
}

.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  margin-bottom: 12px;
}

.skeleton-title {
  height: 24px;
  width: 200px;
  margin: 0 auto 20px;
}

.skeleton-item {
  height: 60px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin: 0 0 8px;
  color: var(--text-primary, #333);
}

.empty-state p {
  margin: 0;
  color: var(--text-secondary, #666);
}

.documents-list {
  padding: 12px;
}

.document-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.document-item:hover {
  background: var(--bg-hover, #f9f9f9);
}

.doc-icon {
  font-size: 2rem;
}

.doc-info {
  flex: 1;
  min-width: 0;
}

.doc-name {
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-meta {
  display: flex;
  gap: 16px;
  font-size: 0.875rem;
  color: var(--text-secondary, #666);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.doc-actions {
  display: flex;
  gap: 8px;
}

.btn-icon-only {
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  border-radius: 6px;
  font-size: 1rem;
  transition: background 0.2s;
}

.btn-icon-only:hover {
  background: var(--bg-secondary, #f0f0f0);
}

.btn-icon-only.danger:hover {
  background: #fee;
}

.modal-overlay {
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

.modal-content {
  background: var(--card-bg, #fff);
  border-radius: 12px;
  max-width: 800px;
  width: 90%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.document-viewer {
  max-width: 900px;
}

.delete-confirm {
  max-width: 400px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #eee);
}

.modal-header h3 {
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-secondary, #666);
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.markdown-content {
  line-height: 1.8;
}

.markdown-content :deep(h1) {
  font-size: 1.75rem;
  margin: 1em 0 0.5em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid var(--border-color, #eee);
}

.markdown-content :deep(h2) {
  font-size: 1.5rem;
  margin: 1em 0 0.5em;
}

.markdown-content :deep(h3) {
  font-size: 1.25rem;
  margin: 1em 0 0.5em;
}

.markdown-content :deep(code) {
  background: var(--bg-secondary, #f5f5f5);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.markdown-content :deep(pre) {
  background: var(--bg-secondary, #f5f5f5);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color, #eee);
}

.doc-stats {
  display: flex;
  gap: 20px;
  font-size: 0.875rem;
  color: var(--text-secondary, #666);
}

.warning-text {
  color: #e74c3c;
  font-size: 0.875rem;
}

.loading-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 12px;
}

.dot {
  width: 12px;
  height: 12px;
  background: var(--primary-color, #4a90d9);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>

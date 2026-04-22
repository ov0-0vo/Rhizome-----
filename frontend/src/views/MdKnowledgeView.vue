<template>
  <div class="md-knowledge-view">
    <div class="card">
      <div class="card-header">
        <div class="header-left">
          <h2>📝 MD知识库</h2>
          <span class="doc-count" v-if="stats">
            {{ stats.total_documents }} 篇文档 / {{ stats.pending_proposals }} 待审核
          </span>
        </div>
        <div class="header-actions">
          <button class="btn btn-primary" @click="showCreateModal = true">
            <span class="btn-icon">➕</span>
            <span class="btn-text">新建文档</span>
          </button>
          <button class="btn btn-secondary" @click="showProposalsPanel = true" v-if="pendingProposals.length > 0">
            <span class="btn-icon">🔔</span>
            <span class="badge">{{ pendingProposals.length }}</span>
          </button>
          <button class="btn btn-secondary" @click="loadData">
            <span class="btn-icon">🔄</span>
          </button>
        </div>
      </div>

      <div class="search-bar">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索文档..."
          class="search-input"
          @input="handleSearch"
        />
      </div>

      <div v-if="loading" class="loading-state">
        <div class="skeleton skeleton-title"></div>
        <div class="skeleton skeleton-item"></div>
        <div class="skeleton skeleton-item"></div>
      </div>

      <div v-else-if="filteredDocuments.length === 0" class="empty-state">
        <div class="empty-icon">📝</div>
        <h3>暂无文档</h3>
        <p>点击"新建文档"创建您的第一篇知识文档</p>
      </div>

      <div v-else class="documents-list">
        <div
          v-for="doc in filteredDocuments"
          :key="doc.id"
          class="document-item"
          @click="editDocument(doc)"
        >
          <div class="doc-icon">📝</div>
          <div class="doc-info">
            <div class="doc-name">{{ doc.title }}</div>
            <div class="doc-meta">
              <span class="meta-item">
                <span class="meta-icon">📅</span>
                {{ formatDate(doc.updated_at) }}
              </span>
              <span class="meta-item">
                <span class="meta-icon">🏷️</span>
                {{ doc.tags?.join(', ') || '无标签' }}
              </span>
              <span class="meta-item">
                <span class="meta-icon">🔒</span>
                受保护
              </span>
            </div>
          </div>
          <div class="doc-actions">
            <button class="btn-icon-only" @click.stop="editDocument(doc)" title="编辑">
              ✏️
            </button>
            <button class="btn-icon-only danger" @click.stop="confirmDelete(doc)" title="删除">
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑文档模态框 -->
    <div v-if="showCreateModal || showEditModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content editor-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ isEditing ? '✏️ 编辑文档' : '➕ 新建文档' }}</h3>
          <button class="btn-close" @click="closeModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>标题</label>
            <input v-model="docForm.title" type="text" class="form-input" placeholder="输入文档标题" />
          </div>
          <div class="form-group">
            <label>标签（用逗号分隔）</label>
            <input v-model="docForm.tags" type="text" class="form-input" placeholder="例如: Python, 后端, 笔记" />
          </div>
          <div class="form-group">
            <label>内容</label>
            <textarea
              v-model="docForm.content"
              class="form-textarea"
              placeholder="输入 Markdown 内容..."
              rows="20"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveDocument">保存</button>
        </div>
      </div>
    </div>

    <!-- 审核提案面板 -->
    <div v-if="showProposalsPanel" class="modal-overlay" @click="showProposalsPanel = false">
      <div class="modal-content proposals-modal" @click.stop>
        <div class="modal-header">
          <h3>🔔 待审核修改</h3>
          <button class="btn-close" @click="showProposalsPanel = false">×</button>
        </div>
        <div class="modal-body">
          <div v-if="pendingProposals.length === 0" class="empty-state">
            <p>暂无待审核的修改提案</p>
          </div>
          <div v-else class="proposals-list">
            <div v-for="proposal in pendingProposals" :key="proposal.id" class="proposal-item">
              <div class="proposal-header">
                <span class="proposal-doc">文档: {{ getDocTitle(proposal.document_id) }}</span>
                <span class="proposal-time">{{ formatDate(proposal.created_at) }}</span>
              </div>
              <div class="proposal-desc">{{ proposal.description || '无描述' }}</div>
              <div class="proposal-actions">
                <button class="btn btn-sm btn-primary" @click="viewProposal(proposal)">查看差异</button>
                <button class="btn btn-sm btn-success" @click="reviewProposal(proposal.id, true)">✅ 批准</button>
                <button class="btn btn-sm btn-danger" @click="reviewProposal(proposal.id, false)">❌ 拒绝</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 查看差异模态框 -->
    <div v-if="showDiffModal" class="modal-overlay" @click="showDiffModal = false">
      <div class="modal-content diff-modal" @click.stop>
        <div class="modal-header">
          <h3>📋 修改差异</h3>
          <button class="btn-close" @click="showDiffModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="diff-container">
            <div class="diff-section">
              <h4>原文</h4>
              <pre class="diff-content original">{{ currentProposal?.original_content }}</pre>
            </div>
            <div class="diff-section">
              <h4>修改后</h4>
              <pre class="diff-content proposed">{{ currentProposal?.proposed_content }}</pre>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDiffModal = false">关闭</button>
          <button class="btn btn-success" @click="reviewProposal(currentProposal.id, true)">✅ 批准</button>
          <button class="btn btn-danger" @click="reviewProposal(currentProposal.id, false)">❌ 拒绝</button>
        </div>
      </div>
    </div>

    <!-- 删除确认 -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="showDeleteConfirm = false">
      <div class="modal-content delete-confirm" @click.stop>
        <div class="modal-header">
          <h3>⚠️ 确认删除</h3>
        </div>
        <div class="modal-body">
          <p>确定要删除文档 <strong>{{ docToDelete?.title }}</strong> 吗？</p>
          <p class="warning-text">此操作不可撤销。</p>
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

const API_BASE = '/api/md-knowledge'

const documents = ref([])
const proposals = ref([])
const stats = ref(null)
const loading = ref(true)
const searchQuery = ref('')

const showCreateModal = ref(false)
const showEditModal = ref(false)
const showProposalsPanel = ref(false)
const showDiffModal = ref(false)
const showDeleteConfirm = ref(false)

const currentDoc = ref(null)
const currentProposal = ref(null)
const docToDelete = ref(null)

const docForm = ref({
  title: '',
  content: '',
  tags: ''
})

const isEditing = computed(() => !!currentDoc.value)

const filteredDocuments = computed(() => {
  if (!searchQuery.value) return documents.value
  const query = searchQuery.value.toLowerCase()
  return documents.value.filter(doc =>
    doc.title?.toLowerCase().includes(query) ||
    doc.content?.toLowerCase().includes(query) ||
    doc.tags?.some(tag => tag.toLowerCase().includes(query))
  )
})

const pendingProposals = computed(() =>
  proposals.value.filter(p => p.status === 'pending')
)

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

function getDocTitle(docId) {
  const doc = documents.value.find(d => d.id === docId)
  return doc?.title || '未知文档'
}

async function apiRequest(method, endpoint, body = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' }
  }
  if (body) options.body = JSON.stringify(body)
  const res = await fetch(`${API_BASE}${endpoint}`, options)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

async function loadData() {
  loading.value = true
  try {
    const [docsRes, proposalsRes, statsRes] = await Promise.all([
      fetch(`${API_BASE}/documents`).then(r => r.json()),
      fetch(`${API_BASE}/proposals`).then(r => r.json()),
      fetch(`${API_BASE}/stats`).then(r => r.json())
    ])
    documents.value = docsRes.documents || []
    proposals.value = proposalsRes.proposals || []
    stats.value = statsRes
  } catch (e) {
    console.error('Failed to load data:', e)
  } finally {
    loading.value = false
  }
}

function editDocument(doc) {
  currentDoc.value = doc
  docForm.value = {
    title: doc.title,
    content: doc.content,
    tags: doc.tags?.join(', ') || ''
  }
  showEditModal.value = true
}

function closeModal() {
  showCreateModal.value = false
  showEditModal.value = false
  currentDoc.value = null
  docForm.value = { title: '', content: '', tags: '' }
}

async function saveDocument() {
  const tags = docForm.value.tags.split(',').map(t => t.trim()).filter(Boolean)
  const payload = {
    title: docForm.value.title,
    content: docForm.value.content,
    tags
  }

  try {
    if (isEditing.value) {
      await apiRequest('PUT', `/documents/${currentDoc.value.id}`, payload)
    } else {
      await apiRequest('POST', '/documents', payload)
    }
    closeModal()
    await loadData()
  } catch (e) {
    console.error('Failed to save document:', e)
    alert('保存失败')
  }
}

function confirmDelete(doc) {
  docToDelete.value = doc
  showDeleteConfirm.value = true
}

async function deleteDocument() {
  if (!docToDelete.value) return
  try {
    await apiRequest('DELETE', `/documents/${docToDelete.value.id}`)
    showDeleteConfirm.value = false
    docToDelete.value = null
    await loadData()
  } catch (e) {
    console.error('Failed to delete document:', e)
    alert('删除失败')
  }
}

function viewProposal(proposal) {
  currentProposal.value = proposal
  showDiffModal.value = true
}

async function reviewProposal(proposalId, approve) {
  try {
    await apiRequest('POST', `/proposals/${proposalId}/review`, { approve, comment: '' })
    showDiffModal.value = false
    await loadData()
  } catch (e) {
    console.error('Failed to review proposal:', e)
    alert('审核失败')
  }
}

let searchTimeout = null
function handleSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
  }, 300)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.md-knowledge-view {
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

.btn-success {
  background: #27ae60;
  color: white;
}

.btn-danger {
  background: #e74c3c;
  color: white;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 0.8rem;
}

.btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.badge {
  background: #e74c3c;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
}

.search-bar {
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-color, #eee);
}

.search-input {
  width: 100%;
  padding: 10px 16px;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 8px;
  font-size: 0.875rem;
  background: var(--bg-primary, #fff);
  color: var(--text-primary, #333);
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color, #4a90d9);
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

.editor-modal {
  max-width: 900px;
  height: 85vh;
}

.proposals-modal {
  max-width: 600px;
}

.diff-modal {
  max-width: 900px;
  height: 80vh;
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

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color, #eee);
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  font-size: 0.875rem;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 8px;
  font-size: 0.875rem;
  background: var(--bg-primary, #fff);
  color: var(--text-primary, #333);
  box-sizing: border-box;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--primary-color, #4a90d9);
}

.form-textarea {
  resize: vertical;
  font-family: monospace;
  line-height: 1.6;
}

.proposals-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.proposal-item {
  padding: 16px;
  border: 1px solid var(--border-color, #eee);
  border-radius: 8px;
}

.proposal-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.proposal-doc {
  font-weight: 500;
}

.proposal-time {
  font-size: 0.8rem;
  color: var(--text-secondary, #666);
}

.proposal-desc {
  font-size: 0.875rem;
  color: var(--text-secondary, #666);
  margin-bottom: 12px;
}

.proposal-actions {
  display: flex;
  gap: 8px;
}

.diff-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  height: 100%;
}

.diff-section {
  display: flex;
  flex-direction: column;
}

.diff-section h4 {
  margin: 0 0 8px;
  font-size: 0.875rem;
  color: var(--text-secondary, #666);
}

.diff-content {
  flex: 1;
  padding: 12px;
  border-radius: 8px;
  font-size: 0.8rem;
  line-height: 1.6;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.diff-content.original {
  background: #fee;
  border: 1px solid #fcc;
}

.diff-content.proposed {
  background: #efe;
  border: 1px solid #cfc;
}

.warning-text {
  color: #e74c3c;
  font-size: 0.875rem;
}
</style>

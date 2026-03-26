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
        <div class="header-actions">
          <button class="btn btn-primary" @click="showCreateModal = true">
            <span class="btn-icon">➕</span>
            <span class="btn-text">新建目录</span>
          </button>
          <button class="btn btn-secondary" @click="loadTree">
            <span class="btn-icon">🔄</span>
            <span class="btn-text">刷新</span>
          </button>
        </div>
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
        <p>点击"新建目录"开始建立您的知识体系</p>
        <button class="btn btn-primary" @click="showCreateModal = true">
          <span class="btn-icon">➕</span>
          新建目录
        </button>
      </div>

      <div v-else class="tree-container">
        <template v-if="tree && tree.id === 'multi-root'">
          <TreeNode 
            v-for="child in tree.children" 
            :key="child.id" 
            :node="child"
            :is-root="true"
            @create-sub-catalog="handleCreateSubCatalog"
            @edit-catalog="handleEditCatalog"
            @delete-catalog="handleDeleteCatalog"
            @add-knowledge="handleAddKnowledge"
            @refresh="loadTree"
          />
        </template>
        <template v-else>
          <TreeNode 
            :node="tree" 
            :is-root="true"
            @create-sub-catalog="handleCreateSubCatalog"
            @edit-catalog="handleEditCatalog"
            @delete-catalog="handleDeleteCatalog"
            @add-knowledge="handleAddKnowledge"
            @refresh="loadTree"
          />
        </template>

        <div class="uncategorized-section" v-if="uncategorizedCount > 0">
          <div class="uncategorized-header" @click="toggleUncategorized">
            <span class="expand-icon">{{ showUncategorized ? '📂' : '📁' }}</span>
            <span class="section-name">未分类</span>
            <span class="knowledge-count">{{ uncategorizedCount }}</span>
          </div>
          <transition name="slide">
            <div v-if="showUncategorized" class="uncategorized-content">
              <div v-if="loadingUncategorized" class="loading-knowledge">
                <div class="loading-dots">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </div>
              </div>
              <div v-else class="knowledge-list">
                <div 
                  v-for="item in uncategorizedKnowledge" 
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
                  <div class="knowledge-actions" @click.stop>
                    <button class="knowledge-action-btn" title="编辑" @click="editUncategorizedKnowledge(item)">
                      <span>✏️</span>
                    </button>
                    <button class="knowledge-action-btn delete" title="删除" @click="confirmDeleteUncategorizedKnowledge(item)">
                      <span>🗑️</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingCatalog ? '编辑目录' : '新建目录' }}</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>目录名称</label>
            <input 
              v-model="formData.name" 
              type="text" 
              placeholder="请输入目录名称"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label>关键词（可选，用逗号分隔）</label>
            <input 
              v-model="keywordsInput" 
              type="text" 
              placeholder="如：Python, 编程, 机器学习"
              class="form-input"
            />
          </div>
          <div class="form-group" v-if="parentCatalogName">
            <label>父目录</label>
            <div class="parent-info">{{ parentCatalogName }}</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="submitForm" :disabled="!formData.name.trim()">
            {{ editingCatalog ? '保存' : '创建' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="selectedKnowledge && !editingKnowledge" class="modal-overlay" @click.self="selectedKnowledge = null">
      <div class="modal knowledge-detail-modal">
        <div class="modal-header">
          <h3>{{ selectedKnowledge.question }}</h3>
          <button class="close-btn" @click="selectedKnowledge = null">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <div class="detail-label">答案</div>
            <div class="detail-content" v-html="formatMarkdown(selectedKnowledge.answer)"></div>
          </div>
          <div class="detail-section" v-if="selectedKnowledge.keywords && selectedKnowledge.keywords.length">
            <div class="detail-label">关键词</div>
            <div class="keywords-list">
              <span class="keyword-tag" v-for="kw in selectedKnowledge.keywords" :key="kw">{{ kw }}</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="selectedKnowledge = null">关闭</button>
          <button class="btn btn-primary" @click="editUncategorizedKnowledge(selectedKnowledge)">编辑</button>
        </div>
      </div>
    </div>

    <div v-if="editingKnowledge" class="modal-overlay" @click.self="editingKnowledge = null">
      <div class="modal knowledge-edit-modal">
        <div class="modal-header">
          <h3>编辑知识</h3>
          <button class="close-btn" @click="editingKnowledge = null">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>问题</label>
            <input v-model="knowledgeForm.question" type="text" class="form-input" placeholder="请输入问题" />
          </div>
          <div class="form-group">
            <label>答案</label>
            <textarea v-model="knowledgeForm.answer" class="form-textarea" placeholder="请输入答案" rows="6"></textarea>
          </div>
          <div class="form-group">
            <label>关键词（用逗号分隔）</label>
            <input v-model="knowledgeKeywordsInput" type="text" class="form-input" placeholder="如：Python, 编程" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="editingKnowledge = null">取消</button>
          <button class="btn btn-primary" @click="saveKnowledge" :disabled="savingKnowledge">
            {{ savingKnowledge ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认删除</h3>
          <button class="close-btn" @click="showDeleteConfirm = false">×</button>
        </div>
        <div class="modal-body">
          <p>确定要删除这条知识吗？</p>
          <div class="delete-preview" v-if="deletingKnowledge">
            <strong>{{ deletingKnowledge.question }}</strong>
          </div>
          <p class="warning-text">此操作不可撤销</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDeleteConfirm = false">取消</button>
          <button class="btn btn-danger" @click="deleteKnowledge" :disabled="deleting">
            {{ deleting ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import { catalogApi, knowledgeApi } from '../api'
import TreeNode from '../components/TreeNode.vue'

const tree = ref(null)
const loading = ref(false)
const showCreateModal = ref(false)
const editingCatalog = ref(null)
const parentCatalogId = ref(null)
const parentCatalogName = ref('')
const keywordsInput = ref('')
const showUncategorized = ref(false)
const uncategorizedCount = ref(0)
const uncategorizedKnowledge = ref([])
const loadingUncategorized = ref(false)
const selectedKnowledge = ref(null)
const editingKnowledge = ref(null)
const savingKnowledge = ref(false)
const showDeleteConfirm = ref(false)
const deletingKnowledge = ref(null)
const deleting = ref(false)

const knowledgeForm = ref({
  id: null,
  question: '',
  answer: '',
  keywords: []
})

const knowledgeKeywordsInput = computed({
  get: () => knowledgeForm.value.keywords.join(', '),
  set: (val) => {
    knowledgeForm.value.keywords = val.split(',').map(k => k.trim()).filter(k => k)
  }
})

const formData = ref({
  name: '',
  keywords: []
})

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
    await loadUncategorizedCount()
  } catch (error) {
    console.error('Failed to load catalog tree:', error)
  } finally {
    loading.value = false
  }
}

const loadUncategorizedCount = async () => {
  try {
    const response = await knowledgeApi.getUncategorizedCount()
    uncategorizedCount.value = response.data.count
  } catch (error) {
    console.error('Failed to load uncategorized count:', error)
  }
}

const toggleUncategorized = async () => {
  showUncategorized.value = !showUncategorized.value
  if (showUncategorized.value && uncategorizedKnowledge.value.length === 0) {
    await loadUncategorizedKnowledge()
  }
}

const loadUncategorizedKnowledge = async () => {
  loadingUncategorized.value = true
  try {
    const response = await knowledgeApi.getUncategorized()
    uncategorizedKnowledge.value = response.data || []
  } catch (error) {
    console.error('Failed to load uncategorized knowledge:', error)
    uncategorizedKnowledge.value = []
  } finally {
    loadingUncategorized.value = false
  }
}

const formatMarkdown = (text) => {
  if (!text) return ''
  return marked(text)
}

const editUncategorizedKnowledge = (item) => {
  selectedKnowledge.value = null
  editingKnowledge.value = item.id
  knowledgeForm.value = {
    id: item.id,
    question: item.question,
    answer: item.answer,
    keywords: item.keywords || []
  }
}

const confirmDeleteUncategorizedKnowledge = (item) => {
  deletingKnowledge.value = item
  showDeleteConfirm.value = true
}

const saveKnowledge = async () => {
  if (!knowledgeForm.value.question.trim() || !knowledgeForm.value.answer.trim()) {
    alert('请填写问题和答案')
    return
  }

  savingKnowledge.value = true
  try {
    await knowledgeApi.update(knowledgeForm.value.id, {
      question: knowledgeForm.value.question,
      answer: knowledgeForm.value.answer,
      keywords: knowledgeForm.value.keywords
    })
    editingKnowledge.value = null
    await loadUncategorizedKnowledge()
    await loadUncategorizedCount()
  } catch (error) {
    console.error('Failed to save knowledge:', error)
    alert('保存失败')
  } finally {
    savingKnowledge.value = false
  }
}

const deleteKnowledge = async () => {
  if (!deletingKnowledge.value) return

  deleting.value = true
  try {
    await knowledgeApi.delete(deletingKnowledge.value.id)
    showDeleteConfirm.value = false
    deletingKnowledge.value = null
    await loadUncategorizedKnowledge()
    await loadUncategorizedCount()
  } catch (error) {
    console.error('Failed to delete knowledge:', error)
    alert('删除失败')
  } finally {
    deleting.value = false
  }
}

const openCreateModal = (parentId = null, parentName = '') => {
  parentCatalogId.value = parentId
  parentCatalogName.value = parentName
  editingCatalog.value = null
  formData.value = { name: '', keywords: [] }
  keywordsInput.value = ''
  showCreateModal.value = true
}

const handleCreateSubCatalog = ({ parentId, parentName }) => {
  openCreateModal(parentId, parentName)
}

const handleEditCatalog = ({ catalogId, name, keywords }) => {
  editingCatalog.value = catalogId
  parentCatalogId.value = null
  parentCatalogName.value = ''
  formData.value = { name, keywords: keywords || [] }
  keywordsInput.value = (keywords || []).join(', ')
  showCreateModal.value = true
}

const handleDeleteCatalog = async ({ catalogId, catalogName }) => {
  if (!confirm(`确定要删除目录"${catalogName}"吗？该目录下的知识将变为未分类状态。`)) {
    return
  }
  
  try {
    await catalogApi.delete(catalogId)
    loadTree()
  } catch (error) {
    console.error('Failed to delete catalog:', error)
    alert('删除失败')
  }
}

const handleAddKnowledge = ({ catalogId }) => {
  console.log('Add knowledge to catalog:', catalogId)
}

const closeModal = () => {
  showCreateModal.value = false
  editingCatalog.value = null
  parentCatalogId.value = null
  parentCatalogName.value = ''
  formData.value = { name: '', keywords: [] }
  keywordsInput.value = ''
}

const submitForm = async () => {
  const keywords = keywordsInput.value
    .split(/[,，]/)
    .map(k => k.trim())
    .filter(k => k)
  
  try {
    if (editingCatalog.value) {
      await catalogApi.update(editingCatalog.value, {
        name: formData.value.name,
        keywords
      })
    } else {
      await catalogApi.create({
        name: formData.value.name,
        keywords,
        parent_id: parentCatalogId.value
      })
    }
    closeModal()
    loadTree()
  } catch (error) {
    console.error('Failed to save catalog:', error)
    alert('保存失败')
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

.header-actions {
  display: flex;
  gap: 8px;
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

.btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: var(--radius-lg);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-dark);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.btn-secondary:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
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
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-item {
  height: 48px;
  width: 100%;
  margin-bottom: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
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
  margin-bottom: 20px;
}

.tree-container {
  padding: 8px 0;
}

.uncategorized-section {
  margin-top: 16px;
  border: 1px dashed var(--border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.uncategorized-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  cursor: pointer;
  background: var(--bg-secondary);
  transition: background 0.2s ease;
}

.uncategorized-header:hover {
  background: var(--bg-hover);
}

.uncategorized-header .expand-icon {
  font-size: 16px;
}

.uncategorized-header .section-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.uncategorized-header .knowledge-count {
  font-size: 12px;
  background: var(--warning-color);
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
}

.uncategorized-content {
  padding: 12px;
  background: var(--bg-card);
}

.uncategorized-content .knowledge-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.uncategorized-content .knowledge-item {
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
}

.uncategorized-content .knowledge-item:hover {
  background: var(--bg-hover);
}

.uncategorized-content .knowledge-question {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.uncategorized-content .knowledge-meta {
  font-size: 12px;
  color: var(--text-secondary);
}

.uncategorized-content .knowledge-item {
  position: relative;
}

.uncategorized-content .knowledge-actions {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.uncategorized-content .knowledge-item:hover .knowledge-actions {
  opacity: 1;
}

.knowledge-action-btn {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.knowledge-action-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.knowledge-action-btn.delete:hover {
  background: var(--danger-light);
  color: var(--danger-color);
}

.btn-danger {
  background: var(--danger-color);
  color: white;
}

.btn-danger:hover {
  background: var(--danger-dark);
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.knowledge-detail-modal,
.knowledge-edit-modal {
  max-width: 600px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
}

.detail-content :first-child {
  margin-top: 0;
}

.detail-content :last-child {
  margin-bottom: 0;
}

.keywords-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-tag {
  padding: 4px 12px;
  background: var(--primary-light);
  color: var(--primary-color);
  border-radius: var(--radius-xl);
  font-size: 12px;
  font-weight: 500;
}

.confirm-modal {
  max-width: 400px;
}

.delete-preview {
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin: 12px 0;
  font-size: 14px;
}

.warning-text {
  color: var(--danger-color);
  font-size: 13px;
}

.form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  font-size: 14px;
  resize: vertical;
  min-height: 120px;
  transition: border-color var(--transition-fast);
  font-family: inherit;
}

.form-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
}

.loading-knowledge {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.loading-dots {
  display: flex;
  gap: 6px;
}

.loading-dots .dot {
  width: 8px;
  height: 8px;
  background: var(--primary-color);
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite;
}

.loading-dots .dot:nth-child(1) { animation-delay: 0s; }
.loading-dots .dot:nth-child(2) { animation-delay: 0.2s; }
.loading-dots .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
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
  backdrop-filter: blur(4px);
}

.modal {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  width: 90%;
  max-width: 480px;
  box-shadow: var(--shadow-lg);
  animation: modalIn 0.2s ease;
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-light);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: var(--radius-lg);
  background: transparent;
  color: var(--text-secondary);
  font-size: 24px;
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-primary);
  transition: all var(--transition-fast);
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.parent-info {
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  font-size: 14px;
  color: var(--text-primary);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border-light);
}

@media (max-width: 768px) {
  .btn-text {
    display: none;
  }
  
  .knowledge-count {
    display: none;
  }
  
  .modal {
    width: 95%;
    margin: 16px;
  }
}
</style>

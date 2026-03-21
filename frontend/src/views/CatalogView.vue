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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { catalogApi } from '../api'
import TreeNode from '../components/TreeNode.vue'

const tree = ref(null)
const loading = ref(false)
const showCreateModal = ref(false)
const editingCatalog = ref(null)
const parentCatalogId = ref(null)
const parentCatalogName = ref('')
const keywordsInput = ref('')

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
  } catch (error) {
    console.error('Failed to load catalog tree:', error)
  } finally {
    loading.value = false
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

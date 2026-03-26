<template>
  <div class="config-view">
    <div class="page-header">
      <h1>⚙️ 系统配置</h1>
      <p>配置 LLM、Embedding 和飞书机器人参数</p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载配置中...</p>
    </div>

    <div v-else class="config-grid">
      <div class="config-card">
        <div class="card-title">
          <span class="card-icon">🤖</span>
          <div>
            <h3>LLM 配置</h3>
            <p>大语言模型，用于对话和知识问答</p>
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label>供应商</label>
            <select v-model="config.llm.provider" class="form-select">
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="azure">Azure OpenAI</option>
              <option value="custom">自定义</option>
            </select>
          </div>

          <div class="form-group">
            <label>模型名称</label>
            <input 
              v-model="config.llm.model_name" 
              type="text" 
              class="form-input"
              placeholder="gpt-3.5-turbo"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>API Key</label>
            <div class="input-with-toggle">
              <input 
                v-model="config.llm.api_key" 
                :type="showLlmKey ? 'text' : 'password'"
                class="form-input"
                placeholder="sk-..."
              />
              <button class="toggle-btn" @click="showLlmKey = !showLlmKey">
                {{ showLlmKey ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>Base URL <span class="optional">(可选)</span></label>
            <input 
              v-model="config.llm.base_url" 
              type="text" 
              class="form-input"
              placeholder="https://api.openai.com/v1"
            />
          </div>
        </div>
      </div>

      <div class="config-card">
        <div class="card-title">
          <span class="card-icon">📊</span>
          <div>
            <h3>Embedding 配置</h3>
            <p>向量嵌入模型，用于知识检索</p>
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label>供应商</label>
            <select v-model="config.embedding.provider" class="form-select">
              <option value="local">本地模型</option>
              <option value="openai">OpenAI</option>
              <option value="custom">自定义</option>
            </select>
          </div>

          <div class="form-group">
            <label>模型名称</label>
            <input 
              v-model="config.embedding.model_name" 
              type="text" 
              class="form-input"
              placeholder="BAAI/bge-large-zh-v1.5"
            />
          </div>
        </div>

        <div class="form-row" v-if="config.embedding.provider !== 'local'">
          <div class="form-group">
            <label>API Key</label>
            <div class="input-with-toggle">
              <input 
                v-model="config.embedding.api_key" 
                :type="showEmbeddingKey ? 'text' : 'password'"
                class="form-input"
                placeholder="API Key"
              />
              <button class="toggle-btn" @click="showEmbeddingKey = !showEmbeddingKey">
                {{ showEmbeddingKey ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>Base URL <span class="optional">(可选)</span></label>
            <input 
              v-model="config.embedding.base_url" 
              type="text" 
              class="form-input"
              placeholder="自定义 API 端点"
            />
          </div>
        </div>

        <div class="info-box" v-if="config.embedding.provider === 'local'">
          <span class="info-icon">💡</span>
          <span>本地模型首次使用时会自动下载，请确保网络畅通</span>
        </div>
      </div>

      <div class="config-card">
        <div class="card-title">
          <span class="card-icon">🤖</span>
          <div>
            <h3>飞书机器人配置</h3>
            <p>配置飞书机器人实现消息推送和交互</p>
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label>App ID</label>
            <input 
              v-model="config.feishu.app_id" 
              type="text" 
              class="form-input"
              placeholder="cli_xxxxxxxxxxxx"
            />
          </div>

          <div class="form-group">
            <label>App Secret</label>
            <div class="input-with-toggle">
              <input 
                v-model="config.feishu.app_secret" 
                :type="showFeishuSecret ? 'text' : 'password'"
                class="form-input"
                placeholder="App Secret"
              />
              <button class="toggle-btn" @click="showFeishuSecret = !showFeishuSecret">
                {{ showFeishuSecret ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>
        </div>

        <div class="info-box">
          <span class="info-icon">📖</span>
          <span>请前往 <a href="https://open.feishu.cn" target="_blank">飞书开放平台</a> 创建应用获取凭证</span>
        </div>
      </div>
    </div>

    <div v-if="!loading" class="config-footer">
      <div class="footer-left">
        <div v-if="saveMessage" class="save-message" :class="saveSuccess ? 'success' : 'error'">
          <span class="msg-icon">{{ saveSuccess ? '✅' : '❌' }}</span>
          {{ saveMessage }}
        </div>
      </div>
      <div class="footer-actions">
        <button class="btn btn-secondary" @click="loadConfig">
          <span class="btn-icon">🔄</span>
          重置
        </button>
        <button class="btn btn-primary" @click="saveConfig" :disabled="saving">
          <span class="btn-icon">💾</span>
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { configApi } from '../api'

const loading = ref(true)
const saving = ref(false)
const saveMessage = ref('')
const saveSuccess = ref(false)
const showLlmKey = ref(false)
const showEmbeddingKey = ref(false)
const showFeishuSecret = ref(false)

const config = ref({
  llm: {
    provider: 'openai',
    model_name: '',
    api_key: '',
    base_url: ''
  },
  embedding: {
    provider: 'local',
    model_name: '',
    api_key: '',
    base_url: ''
  },
  feishu: {
    app_id: '',
    app_secret: ''
  }
})

const loadConfig = async () => {
  loading.value = true
  saveMessage.value = ''
  try {
    const response = await configApi.get()
    config.value = response.data
  } catch (error) {
    console.error('Failed to load config:', error)
  } finally {
    loading.value = false
  }
}

const saveConfig = async () => {
  saving.value = true
  saveMessage.value = ''
  
  try {
    await configApi.update(config.value)
    saveMessage.value = '配置已保存，重启服务后生效'
    saveSuccess.value = true
  } catch (error) {
    console.error('Failed to save config:', error)
    saveMessage.value = '保存失败：' + (error.response?.data?.detail || error.message)
    saveSuccess.value = false
  } finally {
    saving.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.config-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.page-header p {
  font-size: 14px;
  color: var(--text-secondary);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px;
  color: var(--text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-light);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.config-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  overflow-y: auto;
  padding-bottom: 24px;
}

.config-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  border: 1px solid var(--border-color);
}

.card-title {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
}

.card-icon {
  font-size: 32px;
  line-height: 1;
}

.card-title h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.card-title p {
  font-size: 13px;
  color: var(--text-secondary);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.optional {
  font-weight: 400;
  color: var(--text-muted);
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: 14px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  transition: border-color var(--transition-fast);
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--primary-color);
}

.form-input::placeholder {
  color: var(--text-muted);
}

.input-with-toggle {
  position: relative;
  display: flex;
  align-items: center;
}

.input-with-toggle .form-input {
  padding-right: 44px;
}

.toggle-btn {
  position: absolute;
  right: 6px;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius);
}

.toggle-btn:hover {
  background: var(--bg-hover);
}

.info-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--primary-light);
  border-radius: var(--radius-lg);
  font-size: 13px;
  color: var(--primary-color);
  margin-top: 16px;
}

.info-icon {
  font-size: 16px;
}

.info-box a {
  color: var(--primary-color);
  text-decoration: underline;
}

.config-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 20px;
  border-top: 1px solid var(--border-light);
  margin-top: 20px;
}

.footer-left {
  flex: 1;
}

.save-message {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: var(--radius-lg);
  font-size: 14px;
}

.save-message.success {
  background: var(--primary-light);
  color: var(--primary-color);
}

.save-message.error {
  background: #FFF2F0;
  color: var(--danger-color);
}

.msg-icon {
  font-size: 16px;
}

.footer-actions {
  display: flex;
  gap: 12px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
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
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-icon {
  font-size: 16px;
}

@media (max-width: 768px) {
  .config-grid {
    grid-template-columns: 1fr;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .config-footer {
    flex-direction: column;
    gap: 16px;
  }
  
  .footer-left {
    width: 100%;
  }
  
  .footer-actions {
    width: 100%;
  }
  
  .btn {
    flex: 1;
    justify-content: center;
  }
}
</style>

<template>
  <div class="reflection-view">
    <div class="page-header">
      <div class="header-left">
        <h1>🧠 知识理解反思</h1>
        <p>通过对话形式加深对知识的理解</p>
      </div>
      <div class="header-actions" v-if="sessionId">
        <button class="btn btn-secondary" @click="startNewSession">
          <span class="btn-icon">🔄</span>
          新对话
        </button>
      </div>
    </div>

    <div class="reflection-content">
      <div class="chat-container">
        <div class="chat-messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="empty-state">
            <div class="empty-icon">💭</div>
            <h3>开始知识反思</h3>
            <p>输入你想理解和反思的知识点，AI 将帮助你分析和深化理解</p>
          </div>

          <div 
            v-for="(msg, index) in messages" 
            :key="index"
            class="message"
            :class="msg.role"
          >
            <div class="message-avatar">
              <span v-if="msg.role === 'user'">👤</span>
              <span v-else-if="msg.role === 'summary'">📝</span>
              <span v-else>🤖</span>
            </div>
            <div class="message-content">
              <div class="message-header">
                <span class="message-role">{{ getMessageRole(msg.role) }}</span>
              </div>
              <div v-if="msg.role === 'assistant' && !msg.content && loading" class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <div v-else class="message-text markdown-content" v-html="formatMarkdown(msg.content)"></div>
            </div>
          </div>
        </div>

        <div class="chat-input-area">
          <div class="input-wrapper">
            <textarea
              v-model="userInput"
              @keydown.enter.exact.prevent="sendMessage"
              placeholder="描述你对某个知识的理解..."
              rows="1"
              ref="inputRef"
              :disabled="archiving"
            ></textarea>
            <button 
              class="send-btn" 
              @click="sendMessage"
              :disabled="!userInput.trim() || loading || archiving"
            >
              发送
            </button>
          </div>
        </div>
      </div>

      <div class="sidebar" v-if="messages.length > 0">
        <div class="sidebar-section">
          <h4>📦 归档知识</h4>
          <p class="archive-hint">点击归档将自动总结对话并分类到合适的知识目录</p>
          <button 
            class="btn btn-primary archive-btn"
            @click="archiveSession"
            :disabled="archiving || !sessionId"
          >
            <span class="btn-icon">📦</span>
            {{ archiving ? '总结中...' : '总结归档' }}
          </button>
        </div>

        <div class="sidebar-section">
          <h4>💡 使用提示</h4>
          <ul class="tips-list">
            <li>描述你对知识点的理解</li>
            <li>AI 会分析并指出偏差</li>
            <li>多轮对话深化理解</li>
            <li>理解充分后点击归档</li>
          </ul>
        </div>

        <div class="sidebar-section" v-if="archiveResult">
          <h4>✅ 已归档</h4>
          <div class="archive-result">
            <div class="result-item" v-if="archiveResult.catalog_name">
              <strong>目录：</strong>
              <p>{{ archiveResult.catalog_name }}</p>
            </div>
            <div class="result-item">
              <strong>问题：</strong>
              <p>{{ archiveResult.question }}</p>
            </div>
            <div class="result-item">
              <strong>答案：</strong>
              <p>{{ archiveResult.answer.substring(0, 200) }}...</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { marked } from 'marked'
import { reflectionApi } from '../api'

const formatMarkdown = (text) => {
  if (!text) return ''
  return marked(text)
}

const getMessageRole = (role) => {
  const roleMap = {
    'user': '你',
    'assistant': 'AI 助手',
    'summary': '知识总结'
  }
  return roleMap[role] || 'AI 助手'
}

const messages = ref([])
const userInput = ref('')
const loading = ref(false)
const archiving = ref(false)
const sessionId = ref(null)
const archiveResult = ref(null)
const messagesContainer = ref(null)
const inputRef = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const startNewSession = () => {
  messages.value = []
  sessionId.value = null
  archiveResult.value = null
  userInput.value = ''
}

const sendMessage = async () => {
  const message = userInput.value.trim()
  if (!message || loading.value || archiving.value) return

  messages.value.push({
    role: 'user',
    content: message
  })
  
  userInput.value = ''
  loading.value = true
  
  await scrollToBottom()

  const assistantMessageIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: ''
  })

  reflectionApi.chatStream(
    sessionId.value || 'new',
    message,
    messages.value.length === 2 ? message.substring(0, 50) : '',
    (chunk) => {
      if (typeof chunk === 'object' && chunk.sessionId) {
        sessionId.value = chunk.sessionId
      } else if (typeof chunk === 'string') {
        messages.value[assistantMessageIndex].content += chunk
        scrollToBottom()
      }
    },
    () => {
      loading.value = false
      scrollToBottom()
    },
    (error) => {
      console.error('Chat error:', error)
      messages.value[assistantMessageIndex].content = '抱歉，发生了错误，请稍后重试。'
      loading.value = false
    }
  )
}

const archiveSession = async () => {
  if (!sessionId.value || archiving.value) return
  
  archiving.value = true
  archiveResult.value = null
  
  const summaryMessageIndex = messages.value.length
  messages.value.push({
    role: 'summary',
    content: ''
  })
  
  await scrollToBottom()
  
  reflectionApi.archiveStream(
    sessionId.value,
    (chunk) => {
      if (typeof chunk === 'string') {
        messages.value[summaryMessageIndex].content += chunk
        scrollToBottom()
      } else if (typeof chunk === 'object' && chunk.done) {
        archiveResult.value = chunk.done
        messages.value[summaryMessageIndex].content += `\n\n---\n\n✅ **归档完成**\n\n**目录：** ${chunk.done.catalog_name || '未分类'}\n\n**问题：** ${chunk.done.question}\n\n知识条目已保存，你可以在知识目录中查看和编辑。`
        scrollToBottom()
      }
    },
    () => {
      archiving.value = false
      sessionId.value = null
    },
    (error) => {
      console.error('Archive error:', error)
      messages.value[summaryMessageIndex].content = '❌ 归档失败：' + error
      archiving.value = false
    }
  )
}

onMounted(() => {
})
</script>

<style scoped>
.reflection-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.header-left p {
  font-size: 14px;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.reflection-content {
  flex: 1;
  display: flex;
  gap: 20px;
  min-height: 0;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  text-align: center;
  padding: 40px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 14px;
  max-width: 300px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant,
.message.summary {
  align-self: flex-start;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  background: var(--bg-secondary);
}

.message.user .message-avatar {
  background: var(--primary-gradient);
}

.message.summary .message-avatar {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.message-content {
  max-width: 75%;
  min-width: 100px;
  display: flex;
  flex-direction: column;
}

.message-header {
  margin-bottom: 6px;
}

.message-role {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
}

.message-text {
  background: var(--bg-secondary);
  padding: 14px 18px;
  border-radius: var(--radius-lg);
  border-top-left-radius: var(--radius-sm);
  line-height: 1.6;
}

.message.user .message-text {
  background: var(--primary-gradient);
  color: white;
  border-radius: var(--radius-lg);
  border-top-right-radius: var(--radius-sm);
}

.message.summary .message-text {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.message.user .message-text :deep(code) {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.message.user .message-text :deep(pre) {
  background: rgba(0, 0, 0, 0.1);
  border-color: rgba(255, 255, 255, 0.1);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.chat-input-area {
  padding: 16px;
  border-top: 1px solid var(--border-light);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper textarea {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: 14px;
  resize: none;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-family: inherit;
  line-height: 1.5;
  max-height: 120px;
}

.input-wrapper textarea:focus {
  outline: none;
  border-color: var(--primary-color);
}

.input-wrapper textarea::placeholder {
  color: var(--text-muted);
}

.input-wrapper textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.send-btn {
  padding: 12px 24px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--radius-lg);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.send-btn:hover:not(:disabled) {
  background: var(--primary-dark);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sidebar {
  width: 280px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  border: 1px solid var(--border-color);
}

.sidebar-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.archive-hint {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  line-height: 1.5;
}

.archive-btn {
  width: 100%;
  justify-content: center;
}

.tips-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tips-list li {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 8px 0;
  border-bottom: 1px solid var(--border-light);
}

.tips-list li:last-child {
  border-bottom: none;
}

.tips-list li::before {
  content: '•';
  margin-right: 8px;
  color: var(--primary-color);
}

.archive-result {
  background: var(--primary-light);
  border-radius: var(--radius-lg);
  padding: 12px;
}

.result-item {
  margin-bottom: 12px;
}

.result-item:last-child {
  margin-bottom: 0;
}

.result-item strong {
  font-size: 12px;
  color: var(--primary-color);
  display: block;
  margin-bottom: 4px;
}

.result-item p {
  font-size: 13px;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.5;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
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

.btn-primary:hover:not(:disabled) {
  background: var(--primary-dark);
}

.btn-primary:disabled {
  opacity: 0.5;
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
  .reflection-content {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
  }
}
</style>

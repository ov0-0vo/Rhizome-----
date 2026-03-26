<template>
  <div class="chat-view">
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0 && !loading" class="empty-state">
        <div class="empty-icon">💬</div>
        <h3>开始对话</h3>
        <p>输入您的问题，开始构建您的知识体系</p>
      </div>
      
      <div 
        v-for="(msg, index) in messages" 
        :key="index" 
        class="message"
        :class="msg.role"
      >
        <div class="message-avatar">
          <span v-if="msg.role === 'user'">👤</span>
          <span v-else>🤖</span>
        </div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-role">{{ msg.role === 'user' ? '你' : 'AI 助手' }}</span>
          </div>
          <div v-if="msg.role === 'assistant' && !msg.content && loading" class="typing-indicator">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
          <div v-else class="message-text markdown-content" v-html="formatMarkdown(msg.content)"></div>
          <div v-if="msg.catalogName" class="catalog-tag">
            <span class="catalog-icon">📁</span>
            {{ msg.catalogName }}
          </div>
        </div>
      </div>
      
      <div v-if="loading && !hasStreamingMessage" class="message assistant">
        <div class="message-avatar">
          <span>🤖</span>
        </div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-role">AI 助手</span>
          </div>
          <div class="typing-indicator">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input-wrapper">
      <div class="chat-input">
        <textarea
          v-model="inputMessage"
          @keydown.enter.exact.prevent="sendMessage"
          placeholder="输入您的问题，按 Enter 发送..."
          rows="2"
          class="input chat-textarea"
        ></textarea>
        <button 
          class="btn btn-primary send-btn" 
          @click="sendMessage"
          :disabled="loading || !inputMessage.trim()"
        >
          <span class="send-icon">➤</span>
          <span class="send-text">发送</span>
        </button>
      </div>
      <div class="input-hint">
        <span>💡 提示：问题越具体，回答越准确</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { marked } from 'marked'
import { chatApi } from '../api'

const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const useStream = ref(true)

const hasStreamingMessage = ref(false)

const formatMarkdown = (text) => {
  return marked(text)
}

const scrollToBottom = (smooth = false) => {
  nextTick(() => {
    if (messagesContainer.value) {
      if (smooth) {
        messagesContainer.value.style.scrollBehavior = 'smooth'
      }
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      if (smooth) {
        messagesContainer.value.style.scrollBehavior = ''
      }
    }
  })
}

const loadHistory = async () => {
  try {
    const response = await chatApi.getHistory(20)
    const historyItems = response.data.reverse()
    
    historyItems.forEach(item => {
      messages.value.push({
        role: 'user',
        content: item.question
      })
      messages.value.push({
        role: 'assistant',
        content: item.answer,
        catalogName: item.catalog_name
      })
    })
    
    scrollToBottom()
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const userMessage = inputMessage.value.trim()
  messages.value.push({ role: 'user', content: userMessage })
  inputMessage.value = ''
  loading.value = true
  scrollToBottom()

  if (useStream.value) {
    sendStreamMessage(userMessage)
  } else {
    sendNormalMessage(userMessage)
  }
}

const sendStreamMessage = (message) => {
  hasStreamingMessage.value = true
  const assistantMessage = { role: 'assistant', content: '', catalogName: null }
  messages.value.push(assistantMessage)
  const messageIndex = messages.value.length - 1

  chatApi.sendStreamPost(
    message,
    (chunk) => {
      messages.value[messageIndex].content += chunk
      scrollToBottom()
    },
    (metadata) => {
      if (metadata && metadata.catalog_name) {
        messages.value[messageIndex].catalogName = metadata.catalog_name
      }
      loading.value = false
      hasStreamingMessage.value = false
      scrollToBottom()
    },
    (error) => {
      messages.value[messageIndex].content = '抱歉，处理您的问题时出现错误：' + error
      loading.value = false
      hasStreamingMessage.value = false
      scrollToBottom()
    }
  )
}

const sendNormalMessage = async (message) => {
  try {
    const response = await chatApi.send(message)
    messages.value.push({
      role: 'assistant',
      content: response.data.answer,
      catalogName: response.data.catalog_name
    })
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，处理您的问题时出现错误：' + (error.response?.data?.detail || error.message)
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
  padding: 0;
  overflow: hidden;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-md);
}

.chat-messages {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 14px;
}

.message {
  display: flex;
  gap: 12px;
  animation: fadeIn 0.3s ease;
}

.message.user {
  flex-direction: row-reverse;
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

.message-content {
  max-width: 75%;
  min-width: 100px;
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

.message.user .message-text :deep(code) {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.message.user .message-text :deep(pre) {
  background: rgba(0, 0, 0, 0.1);
  border-color: rgba(255, 255, 255, 0.1);
}

.catalog-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  padding: 6px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  font-size: 12px;
  color: var(--text-secondary);
}

.catalog-icon {
  font-size: 12px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 14px 18px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border-top-left-radius: var(--radius-sm);
}

.dot {
  width: 8px;
  height: 8px;
  background: var(--text-muted);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.chat-input-wrapper {
  flex-shrink: 0;
  padding: 20px 24px;
  border-top: 1px solid var(--border-light);
  background: var(--bg-card);
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05);
}

.chat-input {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chat-textarea {
  flex: 1;
  resize: none;
  min-height: 48px;
  max-height: 120px;
  padding: 14px 18px;
  font-size: 15px;
  line-height: 1.5;
}

.send-btn {
  height: 48px;
  padding: 0 24px;
  flex-shrink: 0;
}

.send-icon {
  font-size: 16px;
}

.input-hint {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-muted);
}

@media (max-width: 768px) {
  .chat-view {
    border-radius: 0;
    border: none;
    box-shadow: none;
  }
  
  .chat-messages {
    padding: 16px;
    padding-bottom: 8px;
  }
  
  .message-content {
    max-width: 85%;
    min-width: 80px;
  }
  
  .chat-input-wrapper {
    padding: 12px 16px;
    padding-bottom: max(12px, env(safe-area-inset-bottom));
  }
  
  .chat-textarea {
    min-height: 44px;
    padding: 12px 14px;
    font-size: 16px;
  }
  
  .send-btn {
    height: 44px;
    padding: 0 16px;
  }
  
  .send-text {
    display: none;
  }
  
  .input-hint {
    display: none;
  }
}
</style>

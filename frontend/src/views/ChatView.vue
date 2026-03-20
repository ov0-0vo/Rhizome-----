<template>
  <div class="chat-view">
    <div class="chat-messages" ref="messagesContainer">
      <div 
        v-for="(msg, index) in messages" 
        :key="index" 
        class="message"
        :class="msg.role"
      >
        <div class="message-content">
          <div class="message-text" v-html="formatMarkdown(msg.content)"></div>
          <div v-if="msg.catalogName" class="catalog-tag">
            📁 {{ msg.catalogName }}
          </div>
        </div>
      </div>
      <div v-if="loading" class="loading">
        <span class="loading-text">正在思考中...</span>
      </div>
    </div>

    <div class="chat-input">
      <textarea
        v-model="inputMessage"
        @keydown.enter.exact.prevent="sendMessage"
        placeholder="请输入您的问题..."
        rows="2"
        class="input"
      ></textarea>
      <button 
        class="btn btn-primary" 
        @click="sendMessage"
        :disabled="loading || !inputMessage.trim()"
      >
        发送
      </button>
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

const formatMarkdown = (text) => {
  return marked(text)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
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
      scrollToBottom()
    },
    (error) => {
      messages.value[messageIndex].content = '抱歉，处理您的问题时出现错误：' + error
      loading.value = false
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
  height: calc(100vh - 200px);
  min-height: 400px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--card-bg);
  border-radius: 8px;
  margin-bottom: 20px;
}

.message {
  margin-bottom: 16px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.user .message-content {
  background: var(--primary-color);
  color: white;
}

.message.assistant .message-content {
  background: var(--bg-color);
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
}

.message-text {
  word-break: break-word;
}

.catalog-tag {
  margin-top: 8px;
  font-size: 12px;
  opacity: 0.8;
}

.chat-input {
  display: flex;
  gap: 12px;
}

.chat-input .input {
  flex: 1;
  resize: none;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.loading-text {
  color: var(--text-secondary);
  font-style: italic;
}
</style>

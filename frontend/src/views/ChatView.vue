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
      <div v-if="loading" class="loading"></div>
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
import { ref, nextTick } from 'vue'
import { marked } from 'marked'
import { chatApi } from '../api'

const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)

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

const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const userMessage = inputMessage.value.trim()
  messages.value.push({ role: 'user', content: userMessage })
  inputMessage.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const response = await chatApi.send(userMessage)
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
</style>

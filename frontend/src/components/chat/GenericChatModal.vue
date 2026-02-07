<template>
  <Teleport to="body">
    <div v-if="show" class="chat-overlay" @click.self="$emit('close')">
      <div class="chat-modal">
        <div class="chat-header">
          <div class="chat-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <span>Chat with agent</span>
          </div>
          <button class="close-btn" @click="$emit('close')">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="chat-messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="chat-welcome">
            <p>Type a message below to start the conversation.</p>
          </div>

          <template v-for="(msg, index) in messages" :key="index">
            <div :class="['message', msg.role]">
              <div class="message-avatar">
                <template v-if="msg.role === 'user'">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                  </svg>
                </template>
                <template v-else>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                  </svg>
                </template>
              </div>
              <div class="message-content">
                <div class="message-text" v-html="formatMessage(msg.content)"></div>
              </div>
            </div>
          </template>

          <div v-if="isLoading && (messages.length === 0 || messages[messages.length - 1]?.role !== 'assistant')" class="message assistant loading">
            <div class="message-avatar">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>

          <div v-if="error" class="chat-error">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <span>{{ error }}</span>
            <button @click="error = null">Dismiss</button>
          </div>
        </div>

        <div class="chat-input-area">
          <div class="input-row">
            <textarea
              ref="inputField"
              v-model="inputMessage"
              @keydown.enter.exact.prevent="sendMessage"
              placeholder="Type your message..."
              rows="1"
              :disabled="isLoading"
            ></textarea>
            <button
              class="send-btn"
              @click="sendMessage"
              :disabled="!inputMessage.trim() || isLoading"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { chatApi } from '@/services/api'

const props = defineProps({
  show: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['close'])

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const error = ref(null)
const messagesContainer = ref(null)
const inputField = ref(null)

watch(() => props.show, (newVal) => {
  if (newVal) {
    nextTick(() => {
      inputField.value?.focus()
    })
  }
})

watch(() => props.show, (newVal) => {
  if (!newVal) {
    messages.value = []
    inputMessage.value = ''
    error.value = null
  }
})

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

function formatMessage(content) {
  let formatted = content
    .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
  return formatted
}

async function sendMessage() {
  const message = inputMessage.value.trim()
  if (!message || isLoading.value) return

  messages.value.push({ role: 'user', content: message })
  messages.value.push({ role: 'assistant', content: '' })
  inputMessage.value = ''
  scrollToBottom()

  isLoading.value = true
  error.value = null

  const history = messages.value.slice(0, -2).map(m => ({ role: m.role, content: m.content }))

  await chatApi.genericChatStream(
    message,
    history,
    (text) => {
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'assistant') {
        last.content += text
        scrollToBottom()
      }
    },
    () => {
      isLoading.value = false
      scrollToBottom()
    },
    (err) => {
      console.error('Generic chat stream error:', err)
      error.value = err.message || err.response?.data?.detail || 'Failed to get response. Please try again.'
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'assistant') messages.value.pop()
      isLoading.value = false
    }
  )
}
</script>

<style scoped>
.chat-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.chat-modal {
  background: #0f172a;
  border-radius: 16px;
  width: 100%;
  max-width: 850px;
  height: 80vh;
  max-height: 750px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  border: 1px solid #1e293b;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #1e293b;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 16px 16px 0 0;
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  color: #f1f5f9;
  font-weight: 600;
  font-size: 1.0625rem;
}

.chat-title svg {
  color: #3b82f6;
}

.close-btn {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.375rem;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  color: #f1f5f9;
  background: #1e293b;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.chat-welcome {
  text-align: center;
  padding: 2.5rem 1rem;
  color: #94a3b8;
}

.chat-welcome p {
  margin: 0;
  font-size: 0.9375rem;
}

.message {
  display: flex;
  gap: 0.75rem;
  max-width: 90%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: #3b82f6;
  color: white;
}

.message.assistant .message-avatar {
  background: #64748b;
  color: white;
}

.message-content {
  background: #1e293b;
  padding: 0.875rem 1rem;
  border-radius: 12px;
  color: #e2e8f0;
  font-size: 0.9375rem;
  line-height: 1.6;
}

.message.user .message-content {
  background: #3b82f6;
  color: white;
}

.message-text :deep(pre) {
  background: #0f172a;
  padding: 0.75rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.5rem 0;
}

.message-text :deep(code) {
  background: #334155;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: ui-monospace, monospace;
  font-size: 0.875em;
}

.message-text :deep(pre code) {
  background: transparent;
  padding: 0;
}

.message-text :deep(li) {
  margin-left: 1rem;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 0.25rem 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748b;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

.chat-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #7f1d1d;
  color: #fecaca;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
}

.chat-error button {
  margin-left: auto;
  background: none;
  border: none;
  color: #fecaca;
  cursor: pointer;
  text-decoration: underline;
}

.chat-input-area {
  padding: 1rem 1.25rem;
  border-top: 1px solid #1e293b;
  background: #0f172a;
  border-radius: 0 0 16px 16px;
}

.input-row {
  display: flex;
  gap: 0.75rem;
}

.input-row textarea {
  flex: 1;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  padding: 0.75rem 1rem;
  color: #f1f5f9;
  font-size: 0.9375rem;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  font-family: inherit;
}

.input-row textarea::placeholder {
  color: #64748b;
}

.input-row textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.send-btn {
  background: #3b82f6;
  border: none;
  border-radius: 10px;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #2563eb;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .chat-modal {
    height: 100vh;
    max-height: none;
    border-radius: 0;
  }

  .chat-overlay {
    padding: 0;
  }

  .chat-header {
    border-radius: 0;
  }

  .chat-input-area {
    border-radius: 0;
  }
}
</style>

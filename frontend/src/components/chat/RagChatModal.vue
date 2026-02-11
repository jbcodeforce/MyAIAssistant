<template>
  <Teleport to="body">
    <div v-if="show" class="chat-overlay" @click.self="$emit('close')">
      <div class="chat-modal">
        <div class="chat-header">
          <div class="chat-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              <circle cx="12" cy="10" r="2"/>
              <path d="M12 14v4"/>
            </svg>
            <span>Knowledge Base Assistant</span>
          </div>
          <button class="close-btn" @click="$emit('close')">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <AssistantChatPanel />
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import AssistantChatPanel from '@/components/chat/AssistantChatPanel.vue'

defineProps({
  show: {
    type: Boolean,
    required: true
  }
})

defineEmits(['close'])
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
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #1e293b;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 16px 16px 0 0;
  flex-shrink: 0;
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
  color: #10b981;
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

.chat-modal :deep(.chat-panel) {
  border-radius: 0;
  border: none;
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
}
</style>

<template>
  <Modal
    :show="show"
    :title="title"
    size="large"
    @close="$emit('close')"
  >
    <div v-if="loading" class="notes-doc-modal-loading">
      <p>Loading document...</p>
    </div>
    <div v-else-if="error" class="notes-doc-modal-error">
      <p>{{ error }}</p>
    </div>
    <div
      v-else
      class="markdown-preview view-mode notes-doc-modal-body"
      v-html="html"
      @click="$emit('content-click', $event)"
    ></div>
    <template #footer>
      <button type="button" class="btn-secondary" @click="$emit('close')">Close</button>
    </template>
  </Modal>
</template>

<script setup>
import Modal from '@/components/common/Modal.vue'

defineProps({
  show: {
    type: Boolean,
    required: true
  },
  title: {
    type: String,
    default: ''
  },
  html: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  }
})

defineEmits(['close', 'content-click'])
</script>

<style scoped>
.notes-doc-modal-loading,
.notes-doc-modal-error {
  padding: 2rem;
  text-align: center;
  color: #6b7280;
}

.notes-doc-modal-error p {
  color: #991b1b;
  margin: 0;
}

:global(.dark) .notes-doc-modal-error p {
  color: #fca5a5;
}

.notes-doc-modal-body {
  max-height: 70vh;
  overflow-y: auto;
  padding: 0.25rem 0;
}

.btn-secondary {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  background-color: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

:global(.dark) .btn-secondary {
  background-color: #1e293b;
  color: #f1f5f9;
  border-color: #334155;
}
</style>

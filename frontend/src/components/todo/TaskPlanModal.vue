<template>
  <Teleport to="body">
    <div v-if="show" class="plan-overlay" @click.self="handleClose">
      <div class="plan-modal">
        <div class="plan-header">
          <div class="plan-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
            <span>Task Plan</span>
          </div>
          <button class="close-btn" @click="handleClose">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="plan-task-context">
          <div class="task-badge">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <path d="m9 12 2 2 4-4"/>
            </svg>
            <span>{{ todo.title }}</span>
          </div>
          <p v-if="todo.description" class="task-description">{{ truncatedDescription }}</p>
        </div>

        <div class="plan-content">
          <div v-if="isLoading" class="loading-state">
            <div class="spinner"></div>
            <span>Loading plan...</span>
          </div>

          <div v-else-if="error && !planContent" class="empty-state">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="12" y1="18" x2="12" y2="12"/>
              <line x1="9" y1="15" x2="15" y2="15"/>
            </svg>
            <h3>No Plan Yet</h3>
            <p>Use the AI Planning Assistant to generate a plan, or create one manually below.</p>
          </div>

          <div v-else class="editor-container">
            <div class="editor-toolbar">
              <div class="toolbar-left">
                <button 
                  type="button"
                  class="toolbar-btn"
                  :class="{ active: viewMode === 'edit' }"
                  @click="viewMode = 'edit'"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                  </svg>
                  Edit
                </button>
                <button 
                  type="button"
                  class="toolbar-btn"
                  :class="{ active: viewMode === 'preview' }"
                  @click="viewMode = 'preview'"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                  Preview
                </button>
              </div>
              <div class="toolbar-right">
                <span v-if="hasChanges" class="unsaved-indicator">Unsaved changes</span>
              </div>
            </div>

            <div v-if="viewMode === 'edit'" class="editor-area">
              <textarea
                ref="editorRef"
                v-model="planContent"
                class="markdown-editor"
                placeholder="Write your task plan in Markdown...

## Steps
1. First step
2. Second step

## Notes
- Important note
- Another note"
              ></textarea>
            </div>

            <div v-else class="preview-area">
              <div 
                v-if="planContent" 
                class="content-preview" 
                v-html="renderedPreview"
              ></div>
              <p v-else class="empty-preview">No content to preview</p>
            </div>
          </div>
        </div>

        <div v-if="error" class="plan-error">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>{{ error }}</span>
          <button @click="error = null">Dismiss</button>
        </div>

        <div class="plan-footer">
          <button class="btn-secondary" @click="handleClose">
            Cancel
          </button>
          <button 
            class="btn-primary" 
            @click="savePlan"
            :disabled="isSaving || !hasChanges"
          >
            <svg v-if="isSaving" class="spinner-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
            </svg>
            <span>{{ isSaving ? 'Saving...' : 'Save Plan' }}</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { todosApi } from '@/services/api'
import { marked } from 'marked'

// Configure marked options
marked.setOptions({
  breaks: true,
  gfm: true
})

const props = defineProps({
  show: {
    type: Boolean,
    required: true
  },
  todo: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close'])

const planContent = ref('')
const originalContent = ref('')
const isLoading = ref(false)
const isSaving = ref(false)
const error = ref(null)
const viewMode = ref('edit')
const editorRef = ref(null)

const truncatedDescription = computed(() => {
  if (!props.todo.description) return ''
  return props.todo.description.length > 100
    ? props.todo.description.substring(0, 100) + '...'
    : props.todo.description
})

const hasChanges = computed(() => {
  return planContent.value !== originalContent.value
})

const renderedPreview = computed(() => {
  if (!planContent.value) return ''
  return marked(planContent.value)
})

// Focus editor when switching to edit mode
watch(viewMode, (newMode) => {
  if (newMode === 'edit') {
    nextTick(() => {
      editorRef.value?.focus()
    })
  }
})

// Load plan when modal opens or todo changes
watch(() => [props.show, props.todo.id], ([newShow]) => {
  if (newShow && props.todo.id) {
    loadPlan()
  }
}, { immediate: true })

async function loadPlan() {
  isLoading.value = true
  error.value = null
  planContent.value = ''
  originalContent.value = ''
  viewMode.value = 'edit'

  try {
    const response = await todosApi.getTaskPlan(props.todo.id)
    planContent.value = response.data.content || ''
    originalContent.value = planContent.value
    if (planContent.value) {
      viewMode.value = 'preview'
    }
  } catch (err) {
    if (err.response?.status === 404) {
      // No plan exists yet, that's fine
      planContent.value = ''
      originalContent.value = ''
    } else {
      error.value = err.response?.data?.detail || 'Failed to load task plan'
    }
  } finally {
    isLoading.value = false
  }
}

async function savePlan() {
  if (isSaving.value || !hasChanges.value) return

  isSaving.value = true
  error.value = null

  try {
    await todosApi.saveTaskPlan(props.todo.id, planContent.value)
    originalContent.value = planContent.value
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to save task plan'
  } finally {
    isSaving.value = false
  }
}

function handleClose() {
  if (hasChanges.value) {
    if (!confirm('You have unsaved changes. Discard them?')) {
      return
    }
  }
  emit('close')
}
</script>

<style scoped>
.plan-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.plan-modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 800px;
  height: 80vh;
  max-height: 700px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e5e7eb;
}

.plan-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #111827;
  font-weight: 600;
  font-size: 1rem;
}

.plan-title svg {
  color: #2563eb;
}

.close-btn {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  color: #111827;
  background: #f3f4f6;
}

.plan-task-context {
  padding: 0.75rem 1.25rem;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.task-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #2563eb;
  color: white;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
}

.task-description {
  margin: 0.5rem 0 0 0;
  color: #6b7280;
  font-size: 0.8125rem;
  line-height: 1.4;
}

.plan-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: #6b7280;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #e5e7eb;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.empty-state svg {
  color: #d1d5db;
  margin-bottom: 1rem;
}

.empty-state h3 {
  margin: 0 0 0.5rem 0;
  color: #374151;
  font-size: 1.125rem;
}

.empty-state p {
  margin: 0;
  font-size: 0.875rem;
  max-width: 300px;
}

.editor-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.toolbar-left {
  display: flex;
  gap: 0.25rem;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #6b7280;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.toolbar-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

.toolbar-btn.active {
  background: white;
  color: #2563eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.unsaved-indicator {
  color: #d97706;
  font-size: 0.75rem;
  font-weight: 500;
}

.editor-area {
  flex: 1;
  overflow: auto;
  display: flex;
}

.markdown-editor {
  flex: 1;
  width: 100%;
  padding: 1rem 1.25rem;
  border: none;
  outline: none;
  resize: none;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  color: #374151;
  background: white;
}

.markdown-editor::placeholder {
  color: #9ca3af;
}

.preview-area {
  flex: 1;
  overflow: auto;
  padding: 1rem 1.25rem;
}

.content-preview {
  font-size: 0.9375rem;
  line-height: 1.7;
  color: #374151;
}

.content-preview :deep(h1) {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  color: #111827;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 0.5rem;
}

.content-preview :deep(h2) {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 1.25rem 0 0.75rem 0;
  color: #111827;
}

.content-preview :deep(h3) {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 1rem 0 0.5rem 0;
  color: #374151;
}

.content-preview :deep(p) {
  margin: 0 0 0.75rem 0;
}

.content-preview :deep(ul),
.content-preview :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.content-preview :deep(ul) {
  list-style-type: disc;
}

.content-preview :deep(ol) {
  list-style-type: decimal;
}

.content-preview :deep(li) {
  margin: 0.25rem 0;
}

.content-preview :deep(blockquote) {
  border-left: 3px solid #2563eb;
  margin: 0.75rem 0;
  padding-left: 1rem;
  color: #6b7280;
  font-style: italic;
}

.content-preview :deep(code) {
  background: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: ui-monospace, monospace;
  font-size: 0.875em;
  color: #dc2626;
}

.content-preview :deep(pre) {
  background: #1f2937;
  color: #f9fafb;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.75rem 0;
}

.content-preview :deep(pre code) {
  background: transparent;
  padding: 0;
  color: inherit;
}

.content-preview :deep(strong) {
  font-weight: 600;
  color: #111827;
}

.content-preview :deep(em) {
  font-style: italic;
}

.content-preview :deep(del) {
  text-decoration: line-through;
  color: #9ca3af;
}

.empty-preview {
  color: #9ca3af;
  font-style: italic;
}

.plan-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #fef2f2;
  color: #991b1b;
  padding: 0.75rem 1rem;
  margin: 0 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
}

.plan-error button {
  margin-left: auto;
  background: none;
  border: none;
  color: #991b1b;
  cursor: pointer;
  text-decoration: underline;
  font-size: 0.875rem;
}

.plan-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid #e5e7eb;
}

.btn-primary,
.btn-secondary {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background: #f9fafb;
}

.spinner-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 640px) {
  .plan-modal {
    height: 100vh;
    max-height: none;
    border-radius: 0;
  }
  
  .plan-overlay {
    padding: 0;
  }
}
</style>


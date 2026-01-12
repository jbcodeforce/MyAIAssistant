<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="detail-overlay" @click.self="$emit('close')">
        <div class="detail-modal">
          <div class="detail-header">
            <div class="header-left">
              <StatusIndicator :status="todo.status" />
              <span class="status-text">{{ todo.status }}</span>
            </div>
            <button class="close-btn" @click="$emit('close')">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <div class="detail-content">
            <h1 class="detail-title">{{ todo.title }}</h1>

            <div class="detail-meta">
              <span v-if="todo.category" class="meta-badge category">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M4 7V4h16v3"/>
                  <path d="M9 20h6"/>
                  <path d="M12 4v16"/>
                </svg>
                {{ todo.category }}
              </span>
              <span v-if="todo.due_date" class="meta-badge due-date" :class="dueDateClass">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                {{ formattedDueDate }}
              </span>
              <span v-if="projectName" class="meta-badge project">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
                {{ projectName }}
              </span>
            </div>

            <div v-if="todo.urgency || todo.importance" class="priority-badges">
              <span v-if="todo.urgency" class="priority-badge urgency">
                {{ todo.urgency }}
              </span>
              <span v-if="todo.importance" class="priority-badge importance">
                {{ todo.importance }}
              </span>
            </div>

            <div class="description-section">
              <h3 class="section-title">Description</h3>
              <div 
                v-if="todo.description" 
                class="description-content" 
                v-html="renderedDescription"
              ></div>
              <p v-else class="no-description">No description provided</p>
            </div>

            <div v-if="taskPlan" class="plan-section">
              <h3 class="section-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
                Task Plan
              </h3>
              <div class="plan-content" v-html="renderedTaskPlan"></div>
            </div>
          </div>

          <div class="detail-footer">
            <button class="btn-chat" @click="$emit('chat', todo)">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              AI Assistant
            </button>
            <button class="btn-plan" @click="$emit('plan', todo)">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
              Edit Plan
            </button>
            <button class="btn-edit" @click="$emit('edit', todo)">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
              </svg>
              Edit Task
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { marked } from 'marked'
import { todosApi } from '@/services/api'
import StatusIndicator from './StatusIndicator.vue'

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
  },
  projects: {
    type: Array,
    default: () => []
  }
})

defineEmits(['close', 'edit', 'chat', 'plan'])

const taskPlan = ref('')
const isLoadingPlan = ref(false)

const projectName = computed(() => {
  if (!props.todo.project_id || !props.projects.length) return null
  const project = props.projects.find(p => p.id === props.todo.project_id)
  return project?.name || null
})

const renderedDescription = computed(() => {
  if (!props.todo.description) return ''
  const content = props.todo.description
  const isHtml = content.trim().startsWith('<') || /<[a-z][\s\S]*>/i.test(content)
  
  if (isHtml) {
    return content
  } else {
    return marked(content)
  }
})

const renderedTaskPlan = computed(() => {
  if (!taskPlan.value) return ''
  return marked(taskPlan.value)
})

const formattedDueDate = computed(() => {
  if (!props.todo.due_date) return ''
  const date = new Date(props.todo.due_date)
  return date.toLocaleDateString('en-US', { 
    weekday: 'short',
    month: 'short', 
    day: 'numeric',
    year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
  })
})

const dueDateClass = computed(() => {
  if (!props.todo.due_date) return ''
  const dueDate = new Date(props.todo.due_date)
  const today = new Date()
  const diffDays = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24))
  
  if (diffDays < 0) return 'overdue'
  if (diffDays <= 3) return 'due-soon'
  return 'due-later'
})

// Load task plan when modal opens or todo changes
watch(() => [props.show, props.todo.id], async ([newShow, todoId]) => {
  if (newShow && todoId) {
    await loadTaskPlan()
  }
}, { immediate: true })

async function loadTaskPlan() {
  isLoadingPlan.value = true
  taskPlan.value = ''
  
  try {
    const response = await todosApi.getTaskPlan(props.todo.id)
    taskPlan.value = response.data.content || ''
  } catch (err) {
    if (err.response?.status !== 404) {
      console.error('Failed to load task plan:', err)
    }
    // 404 is expected if no plan exists
  } finally {
    isLoadingPlan.value = false
  }
}
</script>

<style scoped>
.detail-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
  backdrop-filter: blur(4px);
}

.detail-modal {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 720px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

:global(.dark) .detail-modal {
  background: #1e293b;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

:global(.dark) .detail-header {
  background: #0f172a;
  border-color: #334155;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
}

:global(.dark) .status-text {
  color: #94a3b8;
}

.close-btn {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 0.375rem;
  border-radius: 8px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #111827;
  background: #e5e7eb;
}

:global(.dark) .close-btn:hover {
  color: #f1f5f9;
  background: #334155;
}

.detail-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.detail-title {
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  line-height: 1.3;
}

:global(.dark) .detail-title {
  color: #f1f5f9;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.meta-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 500;
}

.meta-badge.category {
  background: #f3f4f6;
  color: #4b5563;
}

:global(.dark) .meta-badge.category {
  background: #334155;
  color: #94a3b8;
}

.meta-badge.due-date {
  background: #e5e7eb;
  color: #6b7280;
}

.meta-badge.due-date.due-soon {
  background: #fef3c7;
  color: #92400e;
}

.meta-badge.due-date.overdue {
  background: #fee2e2;
  color: #991b1b;
}

.meta-badge.project {
  background: #d1fae5;
  color: #047857;
}

:global(.dark) .meta-badge.project {
  background: #064e3b;
  color: #6ee7b7;
}

.priority-badges {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.priority-badge {
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 600;
}

.priority-badge.urgency {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  color: #991b1b;
}

.priority-badge.importance {
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  color: #3730a3;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

:global(.dark) .section-title {
  color: #94a3b8;
}

.description-section {
  margin-bottom: 1.5rem;
}

.description-content {
  font-size: 0.9375rem;
  line-height: 1.7;
  color: #374151;
}

:global(.dark) .description-content {
  color: #e2e8f0;
}

.description-content :deep(p) {
  margin: 0 0 0.75rem 0;
}

.description-content :deep(p:last-child) {
  margin-bottom: 0;
}

.description-content :deep(a) {
  color: #2563eb;
  text-decoration: none;
}

.description-content :deep(a:hover) {
  text-decoration: underline;
}

.description-content :deep(ul),
.description-content :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.description-content :deep(ul) {
  list-style-type: disc;
}

.description-content :deep(ol) {
  list-style-type: decimal;
}

.description-content :deep(li) {
  margin: 0.25rem 0;
}

.description-content :deep(strong),
.description-content :deep(b) {
  font-weight: 600;
  color: #111827;
}

:global(.dark) .description-content :deep(strong),
:global(.dark) .description-content :deep(b) {
  color: #f1f5f9;
}

.description-content :deep(em),
.description-content :deep(i) {
  font-style: italic;
}

.description-content :deep(code) {
  background: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.875em;
  color: #dc2626;
}

:global(.dark) .description-content :deep(code) {
  background: #334155;
  color: #fb7185;
}

.description-content :deep(pre) {
  background: #1f2937;
  color: #f9fafb;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.75rem 0;
}

.description-content :deep(pre code) {
  background: transparent;
  padding: 0;
  color: inherit;
}

.description-content :deep(blockquote) {
  border-left: 3px solid #2563eb;
  margin: 0.75rem 0;
  padding-left: 1rem;
  color: #6b7280;
  font-style: italic;
}

/* Task List (Checkbox) Styles */
.description-content :deep(ul[data-type="taskList"]) {
  list-style: none;
  padding-left: 0;
  margin: 0.5rem 0;
}

.description-content :deep(ul[data-type="taskList"] li) {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin: 0.375rem 0;
}

.description-content :deep(ul[data-type="taskList"] li > label) {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  user-select: none;
  margin-top: 0.2em;
}

.description-content :deep(ul[data-type="taskList"] li > label input[type="checkbox"]) {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #2563eb;
  border-radius: 4px;
}

.description-content :deep(ul[data-type="taskList"] li > div) {
  flex: 1;
  min-width: 0;
}

.description-content :deep(ul[data-type="taskList"] li[data-checked="true"] > div) {
  text-decoration: line-through;
  color: #9ca3af;
}

:global(.dark) .description-content :deep(ul[data-type="taskList"] li[data-checked="true"] > div) {
  color: #64748b;
}

/* Nested task lists */
.description-content :deep(ul[data-type="taskList"] ul[data-type="taskList"]) {
  margin-left: 1.5rem;
  margin-top: 0.25rem;
  margin-bottom: 0;
}

.no-description {
  color: #9ca3af;
  font-style: italic;
  margin: 0;
}

.plan-section {
  padding-top: 1.25rem;
  border-top: 1px solid #e5e7eb;
}

:global(.dark) .plan-section {
  border-color: #334155;
}

.plan-content {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1rem;
  font-size: 0.9375rem;
  line-height: 1.7;
  color: #374151;
}

:global(.dark) .plan-content {
  background: #0f172a;
  color: #e2e8f0;
}

.plan-content :deep(h1),
.plan-content :deep(h2),
.plan-content :deep(h3) {
  margin-top: 0.75rem;
  margin-bottom: 0.5rem;
  color: #111827;
}

:global(.dark) .plan-content :deep(h1),
:global(.dark) .plan-content :deep(h2),
:global(.dark) .plan-content :deep(h3) {
  color: #f1f5f9;
}

.plan-content :deep(h1:first-child),
.plan-content :deep(h2:first-child),
.plan-content :deep(h3:first-child) {
  margin-top: 0;
}

.plan-content :deep(ul) {
  list-style-type: disc;
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.plan-content :deep(ol) {
  list-style-type: decimal;
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.plan-content :deep(li) {
  display: list-item;
  margin: 0.25rem 0;
}

/* Task List (Checkbox) Styles in Plan Content */
.plan-content :deep(ul[data-type="taskList"]) {
  list-style: none;
  padding-left: 0;
}

.plan-content :deep(ul[data-type="taskList"] li) {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.plan-content :deep(ul[data-type="taskList"] li > label) {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  margin-top: 0.2em;
}

.plan-content :deep(ul[data-type="taskList"] li > label input[type="checkbox"]) {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #2563eb;
}

.plan-content :deep(ul[data-type="taskList"] li > div) {
  flex: 1;
  min-width: 0;
}

.plan-content :deep(ul[data-type="taskList"] li[data-checked="true"] > div) {
  text-decoration: line-through;
  color: #9ca3af;
}

:global(.dark) .plan-content :deep(ul[data-type="taskList"] li[data-checked="true"] > div) {
  color: #64748b;
}

.detail-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

:global(.dark) .detail-footer {
  background: #0f172a;
  border-color: #334155;
}

.btn-chat,
.btn-plan,
.btn-edit {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-chat {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
}

.btn-chat:hover {
  background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.35);
}

.btn-plan {
  background: white;
  color: #2563eb;
  border: 1px solid #2563eb;
}

:global(.dark) .btn-plan {
  background: transparent;
  color: #60a5fa;
  border-color: #3b82f6;
}

.btn-plan:hover {
  background: #eff6ff;
}

:global(.dark) .btn-plan:hover {
  background: #1e3a5f;
}

.btn-edit {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

:global(.dark) .btn-edit {
  background: transparent;
  color: #e2e8f0;
  border-color: #475569;
}

.btn-edit:hover {
  background: #f3f4f6;
}

:global(.dark) .btn-edit:hover {
  background: #334155;
}

/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .detail-modal,
.modal-leave-active .detail-modal {
  transition: transform 0.25s ease;
}

.modal-enter-from .detail-modal {
  transform: scale(0.95) translateY(10px);
}

.modal-leave-to .detail-modal {
  transform: scale(0.95) translateY(10px);
}

@media (max-width: 640px) {
  .detail-modal {
    max-height: 100vh;
    border-radius: 0;
  }
  
  .detail-overlay {
    padding: 0;
  }

  .detail-footer {
    flex-direction: column;
  }

  .btn-chat,
  .btn-plan,
  .btn-edit {
    justify-content: center;
  }
}
</style>


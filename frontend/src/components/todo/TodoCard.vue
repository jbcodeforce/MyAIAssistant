<template>
  <div 
    class="todo-card"
    :class="{ 'dragging': isDragging }"
    draggable="true"
    @dragstart="onDragStart"
    @dragend="onDragEnd"
    @click="$emit('click', todo)"
    @dblclick.stop="$emit('view', todo)"
  >
    <div class="todo-header">
      <StatusIndicator :status="todo.status" />
      <div class="todo-actions">
        <button 
          class="action-btn view-btn" 
          @click.stop="$emit('view', todo)"
          title="View Details"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </button>
        <span v-if="todo.project_id && projectName" :title="'Project: ' + projectName" class="project-tooltip-wrapper">
          <router-link 
            :to="`/projects/${todo.project_id}/todos`"
            class="action-btn project-btn"
            @click.stop
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
          </router-link>
        </span>
        <button 
          class="action-btn chat-btn" 
          @click.stop="$emit('chat', todo)"
          title="AI Planning Assistant"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a10 10 0 0 1 10 10c0 5.52-4.48 10-10 10a10 10 0 0 1-10-10 10 10 0 0 1 10-10Z"/>
            <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
            <line x1="9" y1="9" x2="9.01" y2="9"/>
            <line x1="15" y1="9" x2="15.01" y2="9"/>
          </svg>
        </button>
        <button 
          class="action-btn" 
          @click.stop="$emit('edit', todo)"
          title="Edit"
        >
          ✏️
        </button>
        <button 
          class="action-btn" 
          @click.stop="$emit('delete', todo)"
          title="Delete"
        >
          🗑️
        </button>
      </div>
    </div>
    
    <h4 class="todo-title">{{ todo.title }}</h4>
    
    <div v-if="todo.description" class="todo-description" v-html="renderedDescription"></div>
    
    <div class="todo-meta">
      <span v-if="todo.category" class="todo-category">
        {{ todo.category }}
      </span>
      <span v-if="todo.due_date" class="todo-due-date" :class="dueDateClass">
        {{ formattedDueDate }}
      </span>
    </div>
    
    <div class="todo-priority" v-if="todo.urgency || todo.importance">
      <span v-if="todo.urgency" class="priority-badge urgency">
        {{ todo.urgency }}
      </span>
      <span v-if="todo.importance" class="priority-badge importance">
        {{ todo.importance }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { marked } from 'marked'
import StatusIndicator from './StatusIndicator.vue'

const props = defineProps({
  todo: {
    type: Object,
    required: true
  },
  projects: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['click', 'view', 'edit', 'delete', 'chat', 'plan', 'dragstart', 'dragend'])

const isDragging = ref(false)

const projectName = computed(() => {
  if (!props.todo.project_id || !props.projects.length) return null
  const project = props.projects.find(p => p.id === props.todo.project_id)
  return project?.name || null
})

const renderedDescription = computed(() => {
  if (!props.todo.description) return ''
  // If content is already HTML (starts with < or contains HTML tags), use it directly
  // Otherwise, treat as markdown
  const content = props.todo.description
  const isHtml = content.trim().startsWith('<') || /<[a-z][\s\S]*>/i.test(content)
  
  if (isHtml) {
    // Truncate HTML content (strip tags for length check, but keep rendered)
    const stripped = content.replace(/<[^>]*>/g, '')
    if (stripped.length > 120) {
      // Return truncated version with ellipsis
      return content.substring(0, 200) + '...'
    }
    return content
  } else {
    // Parse as markdown
    const truncated = content.length > 120 
      ? content.substring(0, 120) + '...'
      : content
    return marked(truncated)
  }
})

const formattedDueDate = computed(() => {
  if (!props.todo.due_date) return ''
  const date = new Date(props.todo.due_date)
  return date.toLocaleDateString('en-US', { 
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

function onDragStart(event) {
  isDragging.value = true
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('todo-id', props.todo.id.toString())
  emit('dragstart', props.todo)
}

function onDragEnd() {
  isDragging.value = false
  emit('dragend', props.todo)
}
</script>

<style scoped>
.todo-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

:global(.dark) .todo-card {
  background: #1e293b;
  border-color: #334155;
}

.todo-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.todo-card.dragging {
  opacity: 0.5;
}

.todo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.todo-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem;
  opacity: 0.6;
  transition: opacity 0.2s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  opacity: 1;
}

.project-tooltip-wrapper {
  display: inline-flex;
}

.action-btn.view-btn {
  color: #0891b2;
}

.action-btn.view-btn:hover {
  color: #0e7490;
  opacity: 1;
}

.action-btn.project-btn {
  color: #059669;
}

.action-btn.project-btn:hover {
  color: #047857;
  opacity: 1;
}

.action-btn.chat-btn {
  color: #8b5cf6;
}

.action-btn.chat-btn:hover {
  color: #7c3aed;
  opacity: 1;
}

.todo-title {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

:global(.dark) .todo-title {
  color: #f1f5f9;
}

.todo-description {
  margin: 0 0 0.75rem 0;
  font-size: 0.8125rem;
  color: #6b7280;
  line-height: 1.5;
  max-height: 4.5em;
  overflow: hidden;
}

:global(.dark) .todo-description {
  color: #94a3b8;
}

.todo-description :deep(p) {
  margin: 0 0 0.25rem 0;
}

.todo-description :deep(p:last-child) {
  margin-bottom: 0;
}

.todo-description :deep(a) {
  color: #2563eb;
  text-decoration: none;
}

.todo-description :deep(a:hover) {
  text-decoration: underline;
}

.todo-description :deep(ul) {
  list-style-type: disc;
  margin: 0;
  padding-left: 1.25rem;
}

.todo-description :deep(ol) {
  list-style-type: decimal;
  margin: 0;
  padding-left: 1.25rem;
}

.todo-description :deep(li) {
  display: list-item;
  margin: 0.125rem 0;
}

.todo-description :deep(strong),
.todo-description :deep(b) {
  font-weight: 600;
}

.todo-description :deep(em),
.todo-description :deep(i) {
  font-style: italic;
}

.todo-description :deep(code) {
  background: #f3f4f6;
  padding: 0.125rem 0.25rem;
  border-radius: 3px;
  font-family: ui-monospace, monospace;
  font-size: 0.75rem;
}

:global(.dark) .todo-description :deep(code) {
  background: #334155;
}

:global(.dark) .todo-description :deep(a) {
  color: #60a5fa;
}

.todo-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}

.todo-category {
  background-color: #f3f4f6;
  color: #4b5563;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

:global(.dark) .todo-category {
  background-color: #334155;
  color: #94a3b8;
}

.todo-due-date {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.due-soon {
  background-color: #fef3c7;
  color: #92400e;
}

.overdue {
  background-color: #fee2e2;
  color: #991b1b;
}

.due-later {
  background-color: #e5e7eb;
  color: #6b7280;
}

:global(.dark) .due-later {
  background-color: #334155;
  color: #94a3b8;
}

.todo-priority {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.priority-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.priority-badge.urgency {
  background-color: #fef2f2;
  color: #991b1b;
}

.priority-badge.importance {
  background-color: #eef2ff;
  color: #3730a3;
}
</style>

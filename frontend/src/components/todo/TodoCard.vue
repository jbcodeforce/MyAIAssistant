<template>
  <div 
    class="todo-card"
    :class="{ 'dragging': isDragging }"
    draggable="true"
    @dragstart="onDragStart"
    @dragend="onDragEnd"
    @click="$emit('click', todo)"
  >
    <div class="todo-header">
      <StatusIndicator :status="todo.status" />
      <div class="todo-actions">
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
          class="action-btn plan-btn" 
          @click.stop="$emit('plan', todo)"
          title="View/Edit Task Plan"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
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
    
    <p v-if="todo.description" class="todo-description">
      {{ truncatedDescription }}
    </p>
    
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
import StatusIndicator from './StatusIndicator.vue'

const props = defineProps({
  todo: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click', 'edit', 'delete', 'chat', 'plan', 'dragstart', 'dragend'])

const isDragging = ref(false)

const truncatedDescription = computed(() => {
  if (!props.todo.description) return ''
  return props.todo.description.length > 100
    ? props.todo.description.substring(0, 100) + '...'
    : props.todo.description
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
}

.action-btn:hover {
  opacity: 1;
}

.action-btn.chat-btn {
  color: #8b5cf6;
}

.action-btn.chat-btn:hover {
  color: #7c3aed;
  opacity: 1;
}

.action-btn.plan-btn {
  color: #2563eb;
}

.action-btn.plan-btn:hover {
  color: #1d4ed8;
  opacity: 1;
}

.todo-title {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

.todo-description {
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.4;
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


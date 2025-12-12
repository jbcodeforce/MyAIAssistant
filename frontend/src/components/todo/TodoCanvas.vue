<template>
  <div class="todo-canvas">
    <div class="canvas-header">
      <h2>Eisenhower Matrix</h2>
      <p class="canvas-description">Organize your todos by urgency and importance</p>
    </div>
    
    <div class="canvas-grid">
      <div class="axis-label vertical">
        <span>Importance</span>
      </div>
      
      <div class="quadrant-container">
        <div 
          class="quadrant urgent-important"
          @drop="onDrop('Urgent', 'Important')"
          @dragover.prevent
          @dragenter.prevent="onDragEnter('Urgent', 'Important')"
          @dragleave="onDragLeave"
        >
          <div class="quadrant-header">
            <h3>Do First</h3>
            <span class="quadrant-subtitle">Urgent & Important</span>
          </div>
          <div class="quadrant-content">
            <TodoCard
              v-for="todo in urgentImportantTodos"
              :key="todo.id"
              :todo="todo"
              @edit="$emit('edit', todo)"
              @delete="$emit('delete', todo)"
              @chat="$emit('chat', todo)"
              @plan="$emit('plan', todo)"
            />
            <div v-if="urgentImportantTodos.length === 0" class="empty-state">
              Drop todos here
            </div>
          </div>
        </div>
        
        <div 
          class="quadrant not-urgent-important"
          @drop="onDrop('Not Urgent', 'Important')"
          @dragover.prevent
          @dragenter.prevent="onDragEnter('Not Urgent', 'Important')"
          @dragleave="onDragLeave"
        >
          <div class="quadrant-header">
            <h3>Schedule</h3>
            <span class="quadrant-subtitle">Not Urgent & Important</span>
          </div>
          <div class="quadrant-content">
            <TodoCard
              v-for="todo in notUrgentImportantTodos"
              :key="todo.id"
              :todo="todo"
              @edit="$emit('edit', todo)"
              @delete="$emit('delete', todo)"
              @chat="$emit('chat', todo)"
              @plan="$emit('plan', todo)"
            />
            <div v-if="notUrgentImportantTodos.length === 0" class="empty-state">
              Drop todos here
            </div>
          </div>
        </div>
        
        <div 
          class="quadrant urgent-not-important"
          @drop="onDrop('Urgent', 'Not Important')"
          @dragover.prevent
          @dragenter.prevent="onDragEnter('Urgent', 'Not Important')"
          @dragleave="onDragLeave"
        >
          <div class="quadrant-header">
            <h3>Delegate</h3>
            <span class="quadrant-subtitle">Urgent & Not Important</span>
          </div>
          <div class="quadrant-content">
            <TodoCard
              v-for="todo in urgentNotImportantTodos"
              :key="todo.id"
              :todo="todo"
              @edit="$emit('edit', todo)"
              @delete="$emit('delete', todo)"
              @chat="$emit('chat', todo)"
              @plan="$emit('plan', todo)"
            />
            <div v-if="urgentNotImportantTodos.length === 0" class="empty-state">
              Drop todos here
            </div>
          </div>
        </div>
        
        <div 
          class="quadrant not-urgent-not-important"
          @drop="onDrop('Not Urgent', 'Not Important')"
          @dragover.prevent
          @dragenter.prevent="onDragEnter('Not Urgent', 'Not Important')"
          @dragleave="onDragLeave"
        >
          <div class="quadrant-header">
            <h3>Eliminate</h3>
            <span class="quadrant-subtitle">Not Urgent & Not Important</span>
          </div>
          <div class="quadrant-content">
            <TodoCard
              v-for="todo in notUrgentNotImportantTodos"
              :key="todo.id"
              :todo="todo"
              @edit="$emit('edit', todo)"
              @delete="$emit('delete', todo)"
              @chat="$emit('chat', todo)"
              @plan="$emit('plan', todo)"
            />
            <div v-if="notUrgentNotImportantTodos.length === 0" class="empty-state">
              Drop todos here
            </div>
          </div>
        </div>
      </div>
      
      <div class="axis-label horizontal">
        <span>Urgency</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import TodoCard from './TodoCard.vue'

const props = defineProps({
  urgentImportantTodos: {
    type: Array,
    default: () => []
  },
  urgentNotImportantTodos: {
    type: Array,
    default: () => []
  },
  notUrgentImportantTodos: {
    type: Array,
    default: () => []
  },
  notUrgentNotImportantTodos: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update', 'edit', 'delete', 'chat', 'plan'])

const dragOverQuadrant = ref(null)

function onDragEnter(urgency, importance) {
  dragOverQuadrant.value = { urgency, importance }
}

function onDragLeave() {
  dragOverQuadrant.value = null
}

function onDrop(urgency, importance) {
  const event = window.event
  const todoId = parseInt(event.dataTransfer.getData('todo-id'))
  
  if (todoId) {
    emit('update', {
      id: todoId,
      urgency,
      importance
    })
  }
  
  dragOverQuadrant.value = null
}
</script>

<style scoped>
.todo-canvas {
  padding: 2rem;
  width: 100%;
}

.canvas-header {
  text-align: center;
  margin-bottom: 2rem;
}

.canvas-header h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
}

.canvas-description {
  margin: 0;
  color: #6b7280;
  font-size: 1rem;
}

.canvas-grid {
  display: grid;
  grid-template-columns: 40px 1fr;
  grid-template-rows: 1fr 40px;
  gap: 1rem;
  min-height: 600px;
  width: 100%;
}

.axis-label {
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: #4b5563;
  text-transform: uppercase;
  font-size: 0.875rem;
  letter-spacing: 0.05em;
}

.axis-label.vertical {
  writing-mode: vertical-lr;
  transform: rotate(180deg);
}

.axis-label.horizontal {
  grid-column: 1 / -1;
}

.quadrant-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 1rem;
  width: 100%;
}

.quadrant {
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem;
  overflow-y: auto;
  transition: all 0.2s;
  min-width: 0;
  width: 100%;
}

.quadrant:hover {
  border-color: #d1d5db;
}

.quadrant.urgent-important {
  background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
}

.quadrant.not-urgent-important {
  background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 100%);
}

.quadrant.urgent-not-important {
  background: linear-gradient(135deg, #fefce8 0%, #ffffff 100%);
}

.quadrant.not-urgent-not-important {
  background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
}

.quadrant-header {
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #e5e7eb;
}

.quadrant-header h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
}

.quadrant-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.quadrant-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.empty-state {
  padding: 2rem 1rem;
  text-align: center;
  color: #9ca3af;
  font-size: 0.875rem;
  border: 2px dashed #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

@media (max-width: 1024px) {
  .canvas-grid {
    min-height: 800px;
  }
  
  .quadrant-container {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(4, 1fr);
  }
}
</style>


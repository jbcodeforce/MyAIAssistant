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
            <span v-if="urgentImportantTodos.length > 0" class="quadrant-count">{{ urgentImportantTodos.length }}</span>
          </div>
          <div class="quadrant-content" :class="{ 'table-view': urgentImportantTodos.length > 2 }">
            <template v-if="urgentImportantTodos.length <= 2">
              <TodoCard
                v-for="todo in urgentImportantTodos"
                :key="todo.id"
                :todo="todo"
                :projects="projects"
                @view="$emit('view', todo)"
                @edit="$emit('edit', todo)"
                @delete="$emit('delete', todo)"
                @chat="$emit('chat', todo)"
                @plan="$emit('plan', todo)"
              />
            </template>
            <div v-else class="todo-table-wrapper">
              <table class="todo-table">
                <tbody>
                  <tr 
                    v-for="todo in urgentImportantTodos" 
                    :key="todo.id"
                    class="todo-row"
                    draggable="true"
                    @dragstart="onRowDragStart($event, todo)"
                    @dblclick="$emit('view', todo)"
                  >
                    <td class="todo-status-cell">
                      <StatusIndicator :status="todo.status" />
                    </td>
                    <td class="todo-title-cell">{{ todo.title }}</td>
                    <td class="todo-project-cell">
                      <span 
                        v-if="todo.project_id && getProjectName(todo.project_id)"
                        :title="'Project: ' + getProjectName(todo.project_id)"
                        class="project-tooltip-wrapper"
                      >
                        <router-link 
                          :to="`/projects/${todo.project_id}/todos`"
                          class="project-link"
                          @click.stop
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
                        </router-link>
                      </span>
                    </td>
                    <td class="todo-due-cell">
                      <span v-if="todo.due_date" :class="getDueDateClass(todo.due_date)">
                        {{ formatDueDate(todo.due_date) }}
                      </span>
                    </td>
                    <td class="todo-actions-cell">
                      <button class="row-action-btn view" @click.stop="$emit('view', todo)" title="View Details">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                      </button>
                      <button class="row-action-btn" @click.stop="$emit('chat', todo)" title="AI Chat">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 0 1 10 10c0 5.52-4.48 10-10 10a10 10 0 0 1-10-10 10 10 0 0 1 10-10Z"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
                      </button>
                      <button class="row-action-btn" @click.stop="$emit('edit', todo)" title="Edit">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                      </button>
                      <button class="row-action-btn delete" @click.stop="$emit('delete', todo)" title="Delete">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
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
            <span v-if="notUrgentImportantTodos.length > 0" class="quadrant-count">{{ notUrgentImportantTodos.length }}</span>
          </div>
          <div class="quadrant-content" :class="{ 'table-view': notUrgentImportantTodos.length > 2 }">
            <template v-if="notUrgentImportantTodos.length <= 2">
              <TodoCard
                v-for="todo in notUrgentImportantTodos"
                :key="todo.id"
                :todo="todo"
                :projects="projects"
                @view="$emit('view', todo)"
                @edit="$emit('edit', todo)"
                @delete="$emit('delete', todo)"
                @chat="$emit('chat', todo)"
                @plan="$emit('plan', todo)"
              />
            </template>
            <div v-else class="todo-table-wrapper">
              <table class="todo-table">
                <tbody>
                  <tr 
                    v-for="todo in notUrgentImportantTodos" 
                    :key="todo.id"
                    class="todo-row"
                    draggable="true"
                    @dragstart="onRowDragStart($event, todo)"
                    @dblclick="$emit('view', todo)"
                  >
                    <td class="todo-status-cell">
                      <StatusIndicator :status="todo.status" />
                    </td>
                    <td class="todo-title-cell">{{ todo.title }}</td>
                    <td class="todo-project-cell">
                      <span 
                        v-if="todo.project_id && getProjectName(todo.project_id)"
                        :title="'Project: ' + getProjectName(todo.project_id)"
                        class="project-tooltip-wrapper"
                      >
                        <router-link 
                          :to="`/projects/${todo.project_id}/todos`"
                          class="project-link"
                          @click.stop
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
                        </router-link>
                      </span>
                    </td>
                    <td class="todo-due-cell">
                      <span v-if="todo.due_date" :class="getDueDateClass(todo.due_date)">
                        {{ formatDueDate(todo.due_date) }}
                      </span>
                    </td>
                    <td class="todo-actions-cell">
                      <button class="row-action-btn view" @click.stop="$emit('view', todo)" title="View Details">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                      </button>
                      <button class="row-action-btn" @click.stop="$emit('chat', todo)" title="AI Chat">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 0 1 10 10c0 5.52-4.48 10-10 10a10 10 0 0 1-10-10 10 10 0 0 1 10-10Z"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
                      </button>
                      <button class="row-action-btn" @click.stop="$emit('edit', todo)" title="Edit">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                      </button>
                      <button class="row-action-btn delete" @click.stop="$emit('delete', todo)" title="Delete">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
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
            <span v-if="urgentNotImportantTodos.length > 0" class="quadrant-count">{{ urgentNotImportantTodos.length }}</span>
          </div>
          <div class="quadrant-content" :class="{ 'table-view': urgentNotImportantTodos.length > 2 }">
            <template v-if="urgentNotImportantTodos.length <= 2">
              <TodoCard
                v-for="todo in urgentNotImportantTodos"
                :key="todo.id"
                :todo="todo"
                :projects="projects"
                @view="$emit('view', todo)"
                @edit="$emit('edit', todo)"
                @delete="$emit('delete', todo)"
                @chat="$emit('chat', todo)"
                @plan="$emit('plan', todo)"
              />
            </template>
            <div v-else class="todo-table-wrapper">
              <table class="todo-table">
                <tbody>
                  <tr 
                    v-for="todo in urgentNotImportantTodos" 
                    :key="todo.id"
                    class="todo-row"
                    draggable="true"
                    @dragstart="onRowDragStart($event, todo)"
                    @dblclick="$emit('view', todo)"
                  >
                    <td class="todo-status-cell">
                      <StatusIndicator :status="todo.status" />
                    </td>
                    <td class="todo-title-cell">{{ todo.title }}</td>
                    <td class="todo-project-cell">
                      <span 
                        v-if="todo.project_id && getProjectName(todo.project_id)"
                        :title="'Project: ' + getProjectName(todo.project_id)"
                        class="project-tooltip-wrapper"
                      >
                        <router-link 
                          :to="`/projects/${todo.project_id}/todos`"
                          class="project-link"
                          @click.stop
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
                        </router-link>
                      </span>
                    </td>
                    <td class="todo-due-cell">
                      <span v-if="todo.due_date" :class="getDueDateClass(todo.due_date)">
                        {{ formatDueDate(todo.due_date) }}
                      </span>
                    </td>
                    <td class="todo-actions-cell">
                      <button class="row-action-btn view" @click.stop="$emit('view', todo)" title="View Details">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                      </button>
                      <button class="row-action-btn" @click.stop="$emit('chat', todo)" title="AI Chat">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 0 1 10 10c0 5.52-4.48 10-10 10a10 10 0 0 1-10-10 10 10 0 0 1 10-10Z"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
                      </button>
                      <button class="row-action-btn" @click.stop="$emit('edit', todo)" title="Edit">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                      </button>
                      <button class="row-action-btn delete" @click.stop="$emit('delete', todo)" title="Delete">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
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
            <span v-if="notUrgentNotImportantTodos.length > 0" class="quadrant-count">{{ notUrgentNotImportantTodos.length }}</span>
          </div>
          <div class="quadrant-content" :class="{ 'table-view': notUrgentNotImportantTodos.length > 2 }">
            <template v-if="notUrgentNotImportantTodos.length <= 2">
              <TodoCard
                v-for="todo in notUrgentNotImportantTodos"
                :key="todo.id"
                :todo="todo"
                :projects="projects"
                @view="$emit('view', todo)"
                @edit="$emit('edit', todo)"
                @delete="$emit('delete', todo)"
                @chat="$emit('chat', todo)"
                @plan="$emit('plan', todo)"
              />
            </template>
            <div v-else class="todo-table-wrapper">
              <table class="todo-table">
                <tbody>
                  <tr 
                    v-for="todo in notUrgentNotImportantTodos" 
                    :key="todo.id"
                    class="todo-row"
                    draggable="true"
                    @dragstart="onRowDragStart($event, todo)"
                    @dblclick="$emit('view', todo)"
                  >
                    <td class="todo-status-cell">
                      <StatusIndicator :status="todo.status" />
                    </td>
                    <td class="todo-title-cell">{{ todo.title }}</td>
                    <td class="todo-project-cell">
                      <span 
                        v-if="todo.project_id && getProjectName(todo.project_id)"
                        :title="'Project: ' + getProjectName(todo.project_id)"
                        class="project-tooltip-wrapper"
                      >
                        <router-link 
                          :to="`/projects/${todo.project_id}/todos`"
                          class="project-link"
                          @click.stop
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
                        </router-link>
                      </span>
                    </td>
                    <td class="todo-due-cell">
                      <span v-if="todo.due_date" :class="getDueDateClass(todo.due_date)">
                        {{ formatDueDate(todo.due_date) }}
                      </span>
                    </td>
                    <td class="todo-actions-cell">
                      <button class="row-action-btn view" @click.stop="$emit('view', todo)" title="View Details">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                      </button>
                      <button class="row-action-btn" @click.stop="$emit('chat', todo)" title="AI Chat">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 0 1 10 10c0 5.52-4.48 10-10 10a10 10 0 0 1-10-10 10 10 0 0 1 10-10Z"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
                      </button>
                      <button class="row-action-btn" @click.stop="$emit('edit', todo)" title="Edit">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                      </button>
                      <button class="row-action-btn delete" @click.stop="$emit('delete', todo)" title="Delete">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
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
import StatusIndicator from './StatusIndicator.vue'

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
  },
  projects: {
    type: Array,
    default: () => []
  }
})

function getProjectName(projectId) {
  if (!projectId || !props.projects.length) return null
  const project = props.projects.find(p => p.id === projectId)
  return project?.name || null
}

const emit = defineEmits(['update', 'view', 'edit', 'delete', 'chat', 'plan'])

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

function onRowDragStart(event, todo) {
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('todo-id', todo.id.toString())
}

function formatDueDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric'
  })
}

function getDueDateClass(dateStr) {
  if (!dateStr) return ''
  const dueDate = new Date(dateStr)
  const today = new Date()
  const diffDays = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24))
  
  if (diffDays < 0) return 'due-badge overdue'
  if (diffDays <= 3) return 'due-badge due-soon'
  return 'due-badge due-later'
}
</script>

<style scoped>
.todo-canvas {
  padding: 2rem;
  width: 100%;
  display: block;
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
  grid-template-columns: 40px minmax(0, 1fr);
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
  grid-template-columns: repeat(2, minmax(0, 1fr));
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

.quadrant-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.375rem;
  margin-left: 0.5rem;
  background: #e5e7eb;
  color: #4b5563;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 9999px;
}

.quadrant-content.table-view {
  padding: 0;
}

.todo-table-wrapper {
  max-height: 280px;
  overflow-y: auto;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.todo-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.todo-row {
  border-bottom: 1px solid #e5e7eb;
  cursor: grab;
  transition: background-color 0.15s;
}

.todo-row:last-child {
  border-bottom: none;
}

.todo-row:hover {
  background-color: rgba(0, 0, 0, 0.03);
}

.todo-row:active {
  cursor: grabbing;
}

.todo-status-cell {
  width: 32px;
  padding: 0.5rem;
  text-align: center;
}

.todo-title-cell {
  padding: 0.5rem 0.5rem 0.5rem 0;
  font-weight: 500;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.todo-project-cell {
  padding: 0.5rem;
  width: 32px;
  text-align: center;
}

.project-tooltip-wrapper {
  display: inline-flex;
}

.project-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #059669;
  opacity: 0.7;
  transition: all 0.15s;
}

.project-link:hover {
  opacity: 1;
  color: #047857;
}

.todo-due-cell {
  padding: 0.5rem;
  white-space: nowrap;
  width: 80px;
}

.due-badge {
  display: inline-block;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.due-badge.due-soon {
  background-color: #fef3c7;
  color: #92400e;
}

.due-badge.overdue {
  background-color: #fee2e2;
  color: #991b1b;
}

.due-badge.due-later {
  background-color: #e5e7eb;
  color: #6b7280;
}

.todo-actions-cell {
  padding: 0.5rem;
  white-space: nowrap;
  text-align: right;
  width: 120px;
}

.row-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  margin-left: 2px;
  background: none;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.15s;
}

.row-action-btn:hover {
  background-color: #e5e7eb;
  color: #111827;
}

.row-action-btn.view {
  color: #0891b2;
}

.row-action-btn.view:hover {
  background-color: #ecfeff;
  color: #0e7490;
}

.row-action-btn.delete:hover {
  background-color: #fee2e2;
  color: #dc2626;
}

@media (max-width: 1024px) {
  .canvas-grid {
    min-height: 800px;
  }
  
  .quadrant-container {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(4, 1fr);
  }

  .todo-title-cell {
    max-width: 150px;
  }
}
</style>


<template>
  <div class="project-todos-view">
    <div class="view-header">
      <div class="header-left">
        <router-link to="/projects" class="back-link">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
          Back to Projects
        </router-link>
        <div class="header-title">
          <h2 v-if="project">{{ project.name }}</h2>
          <h2 v-else-if="loading">Loading...</h2>
          <h2 v-else>Project Tasks</h2>
          <div class="header-meta">
            <router-link 
              v-if="organization"
              :to="`/organizations/${organization.id}`"
              class="organization-link"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              {{ organization.name }}
            </router-link>
            <span class="view-description">
              Tasks linked to this project
            </span>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <div class="header-stats" v-if="!loading && !error && todos.length > 0">
          <span class="stat-badge open">{{ openCount }} open</span>
          <span class="stat-badge started">{{ startedCount }} started</span>
          <span class="stat-badge completed">{{ completedCount }} completed</span>
        </div>
        <button class="btn-new-todo" @click="openCreateModal">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 5v14"/>
            <path d="M5 12h14"/>
          </svg>
          New Todo
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading project tasks...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadProjectTodos" class="btn-primary">Retry</button>
    </div>

    <div v-else class="todos-content-container">
      <div v-if="todos.length === 0" class="empty-state">
        <p>No tasks linked to this project</p>
        <p class="empty-state-hint">
          Create a task and link it to this project to see it here
        </p>
      </div>

      <div v-else class="table-container">
        <table class="todos-table">
          <thead>
            <tr>
              <th class="col-status">Status</th>
              <th class="col-title">Title</th>
              <th class="col-category">Category</th>
              <th class="col-priority">Priority</th>
              <th class="col-date">Due Date</th>
              <th class="col-date">Created</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="todo in sortedTodos" :key="todo.id" :class="['todo-row', todo.status.toLowerCase()]">
              <td class="col-status">
                <span :class="['status-badge', todo.status.toLowerCase()]">
                  {{ todo.status }}
                </span>
              </td>
              <td class="col-title">
                <span class="todo-title">{{ todo.title }}</span>
                <span v-if="todo.description" class="todo-description">{{ truncate(stripHtml(todo.description), 60) }}</span>
              </td>
              <td class="col-category">
                <span v-if="todo.category" class="category-badge">{{ todo.category }}</span>
                <span v-else class="no-value">-</span>
              </td>
              <td class="col-priority">
                <div class="priority-badges">
                  <span v-if="todo.urgency" :class="['priority-badge', todo.urgency === 'Urgent' ? 'urgent' : 'not-urgent']">
                    {{ todo.urgency }}
                  </span>
                  <span v-if="todo.importance" :class="['priority-badge', todo.importance === 'Important' ? 'important' : 'not-important']">
                    {{ todo.importance }}
                  </span>
                  <span v-if="!todo.urgency && !todo.importance" class="no-value">-</span>
                </div>
              </td>
              <td class="col-date">
                <span v-if="todo.due_date" :class="{ 'overdue': isOverdue(todo) }">
                  {{ formatDate(todo.due_date) }}
                </span>
                <span v-else class="no-value">-</span>
              </td>
              <td class="col-date">{{ formatDate(todo.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="hasMore" class="load-more">
        <button @click="loadMore" class="btn-secondary">
          Load More ({{ todos.length }} of {{ totalCount }})
        </button>
      </div>
    </div>

    <Modal
      :show="showCreateModal"
      title="Create New Todo"
      :wide="true"
      @close="closeCreateModal"
    >
      <TodoForm
        :initial-data="{ project_id: route.params.id }"
        @submit="handleCreate"
        @cancel="closeCreateModal"
      />
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { projectsApi, todosApi, organizationsApi } from '@/services/api'
import { useUiStore } from '@/stores/uiStore'
import Modal from '@/components/common/Modal.vue'
import TodoForm from '@/components/todo/TodoForm.vue'

const uiStore = useUiStore()

const route = useRoute()

const project = ref(null)
const organization = ref(null)
const todos = ref([])
const totalCount = ref(0)
const currentSkip = ref(0)
const limit = 50
const loading = ref(false)
const error = ref(null)
const showCreateModal = ref(false)

const sortedTodos = computed(() => {
  return [...todos.value].sort((a, b) => {
    // Sort by status priority (Open, Started first), then by due date, then by created date
    const statusOrder = { 'Open': 0, 'Started': 1, 'Completed': 2, 'Cancelled': 3 }
    const statusDiff = (statusOrder[a.status] || 99) - (statusOrder[b.status] || 99)
    if (statusDiff !== 0) return statusDiff
    
    // Then by due date (earliest first, nulls last)
    if (a.due_date && b.due_date) {
      return new Date(a.due_date) - new Date(b.due_date)
    }
    if (a.due_date) return -1
    if (b.due_date) return 1
    
    // Then by created date (newest first)
    return new Date(b.created_at) - new Date(a.created_at)
  })
})

const openCount = computed(() => {
  return todos.value.filter(t => t.status === 'Open').length
})

const startedCount = computed(() => {
  return todos.value.filter(t => t.status === 'Started').length
})

const completedCount = computed(() => {
  return todos.value.filter(t => t.status === 'Completed').length
})

const hasMore = computed(() => {
  return todos.value.length < totalCount.value
})

onMounted(() => {
  loadProjectTodos()
})

async function loadProjectTodos() {
  const projectId = route.params.id
  loading.value = true
  error.value = null
  
  try {
    // Load project details
    const projectResponse = await projectsApi.get(projectId)
    project.value = projectResponse.data
    
    // Load organization if project has one
    if (project.value.organization_id) {
      try {
        const orgResponse = await organizationsApi.get(project.value.organization_id)
        organization.value = orgResponse.data
      } catch (orgErr) {
        console.error('Failed to load organization:', orgErr)
        organization.value = null
      }
    } else {
      organization.value = null
    }
    
    // Load todos for the project
    const todosResponse = await projectsApi.getTodos(projectId, { skip: 0, limit })
    todos.value = todosResponse.data.todos
    totalCount.value = todosResponse.data.total
    currentSkip.value = todosResponse.data.todos.length
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load project tasks'
    console.error('Failed to load project tasks:', err)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  const projectId = route.params.id
  try {
    const response = await projectsApi.getTodos(projectId, { skip: currentSkip.value, limit })
    todos.value = [...todos.value, ...response.data.todos]
    currentSkip.value = todos.value.length
  } catch (err) {
    console.error('Failed to load more todos:', err)
  }
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

function isOverdue(todo) {
  if (!todo.due_date || todo.status === 'Completed' || todo.status === 'Cancelled') {
    return false
  }
  return new Date(todo.due_date) < new Date()
}

function truncate(text, maxLength) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

function stripHtml(html) {
  if (!html) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = html
  return tmp.textContent || tmp.innerText || ''
}

function openCreateModal() {
  showCreateModal.value = true
}

function closeCreateModal() {
  showCreateModal.value = false
}

async function handleCreate(todoData) {
  try {
    // Pre-fill the project_id with the current project
    const dataWithProject = {
      ...todoData,
      project_id: route.params.id
    }
    await todosApi.create(dataWithProject)
    closeCreateModal()
    // Reload todos to show the new one
    await loadProjectTodos()
  } catch (err) {
    console.error('Failed to create todo:', err)
  }
}
</script>

<style scoped>
.project-todos-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .project-todos-view {
  background: #0f172a;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  color: #6b7280;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: color 0.15s;
}

.back-link:hover {
  color: #2563eb;
}

:global(.dark) .back-link {
  color: #94a3b8;
}

:global(.dark) .back-link:hover {
  color: #60a5fa;
}

.header-title h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
}

:global(.dark) .header-title h2 {
  color: #f1f5f9;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.organization-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.625rem;
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.15s;
}

.organization-link:hover {
  background: #c7d2fe;
  color: #312e81;
}

.organization-link svg {
  flex-shrink: 0;
}

:global(.dark) .organization-link {
  background: rgba(99, 102, 241, 0.2);
  color: #a5b4fc;
}

:global(.dark) .organization-link:hover {
  background: rgba(99, 102, 241, 0.3);
  color: #c7d2fe;
}

.view-description {
  margin: 0;
  color: #6b7280;
  font-size: 1rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-stats {
  display: flex;
  gap: 0.75rem;
}

.btn-new-todo {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-new-todo:hover {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.35);
}

.btn-new-todo svg {
  width: 18px;
  height: 18px;
}

.stat-badge {
  padding: 0.375rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.stat-badge.open {
  background: #dbeafe;
  color: #1e40af;
}

.stat-badge.started {
  background: #fef3c7;
  color: #92400e;
}

.stat-badge.completed {
  background: #dcfce7;
  color: #166534;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 1rem;
}

.loading-state p,
.error-state p {
  font-size: 1.125rem;
  color: #6b7280;
}

.todos-content-container {
  width: 100%;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 12px;
  border: 2px dashed #e5e7eb;
}

:global(.dark) .empty-state {
  background: #1e293b;
  border-color: #334155;
}

.empty-state p {
  margin: 0;
  font-size: 1.125rem;
  color: #6b7280;
}

.empty-state-hint {
  margin-top: 0.5rem !important;
  font-size: 0.875rem !important;
  color: #9ca3af !important;
}

.table-container {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  width: 100%;
}

:global(.dark) .table-container {
  background: #1e293b;
  border-color: #334155;
}

.todos-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.todos-table th {
  background: #f9fafb;
  padding: 0.875rem 1rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}

:global(.dark) .todos-table th {
  background: #0f172a;
  color: #94a3b8;
  border-bottom-color: #334155;
}

.todos-table td {
  padding: 0.875rem 1rem;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
}

:global(.dark) .todos-table td {
  border-bottom-color: #334155;
}

.todos-table tbody tr:last-child td {
  border-bottom: none;
}

.todos-table tbody tr:hover {
  background: #f9fafb;
}

:global(.dark) .todos-table tbody tr:hover {
  background: #334155;
}

.todo-row.open {
  background: #eff6ff;
}

.todo-row.started {
  background: #fffbeb;
}

.todo-row.completed {
  background: #f0fdf4;
}

.todo-row.cancelled {
  background: #fefce8;
}

:global(.dark) .todo-row.open {
  background: rgba(59, 130, 246, 0.1);
}

:global(.dark) .todo-row.started {
  background: rgba(245, 158, 11, 0.1);
}

:global(.dark) .todo-row.completed {
  background: rgba(16, 185, 129, 0.1);
}

:global(.dark) .todo-row.cancelled {
  background: rgba(234, 179, 8, 0.1);
}

.todo-row.open:hover {
  background: #dbeafe;
}

.todo-row.started:hover {
  background: #fef3c7;
}

.todo-row.completed:hover {
  background: #dcfce7;
}

.todo-row.cancelled:hover {
  background: #fef9c3;
}

.col-status {
  width: 100px;
}

.col-title {
  min-width: 200px;
}

.col-category {
  width: 120px;
}

.col-priority {
  width: 180px;
}

.col-date {
  width: 110px;
  white-space: nowrap;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.status-badge.open {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.started {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.completed {
  background: #dcfce7;
  color: #166534;
}

.status-badge.cancelled {
  background: #fee2e2;
  color: #991b1b;
}

.todo-title {
  display: block;
  font-weight: 500;
  color: #111827;
}

:global(.dark) .todo-title {
  color: #f1f5f9;
}

.todo-description {
  display: block;
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

.category-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

:global(.dark) .category-badge {
  background: rgba(99, 102, 241, 0.2);
  color: #a5b4fc;
}

.no-value {
  color: #9ca3af;
}

.priority-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.priority-badge {
  display: inline-block;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
}

.priority-badge.urgent {
  background: #fee2e2;
  color: #991b1b;
}

.priority-badge.not-urgent {
  background: #f3f4f6;
  color: #6b7280;
}

.priority-badge.important {
  background: #dbeafe;
  color: #1e40af;
}

.priority-badge.not-important {
  background: #f3f4f6;
  color: #6b7280;
}

.overdue {
  color: #dc2626;
  font-weight: 500;
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 1.5rem;
}

.btn-primary,
.btn-secondary {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background-color: #2563eb;
  color: white;
}

.btn-primary:hover {
  background-color: #1d4ed8;
}

.btn-secondary {
  background-color: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

:global(.dark) .btn-secondary {
  background-color: #1e293b;
  color: #f1f5f9;
  border-color: #334155;
}

.btn-secondary:hover {
  background-color: #f9fafb;
}

:global(.dark) .btn-secondary:hover {
  background-color: #334155;
}

@media (max-width: 1024px) {
  .table-container {
    overflow-x: auto;
  }
  
  .todos-table {
    min-width: 800px;
  }
}

@media (max-width: 768px) {
  .project-todos-view {
    padding: 1rem;
  }

  .view-header {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>


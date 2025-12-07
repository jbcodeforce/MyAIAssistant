<template>
  <div class="archived-view">
    <div class="view-header">
      <div>
        <h2>Archived Todos</h2>
        <p class="view-description">
          Completed and cancelled todos
        </p>
      </div>
      <div class="header-stats" v-if="!loading && !error">
        <span class="stat-badge completed">{{ completedCount }} completed</span>
        <span class="stat-badge cancelled">{{ cancelledCount }} cancelled</span>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading archived todos...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadArchived" class="btn-primary">Retry</button>
    </div>

    <div v-else class="archived-content">
      <div v-if="archivedTodos.length === 0" class="empty-state">
        <p>No archived todos</p>
        <p class="empty-state-hint">
          Completed and cancelled todos will appear here
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
              <th class="col-date">Created</th>
              <th class="col-date">Completed</th>
              <th class="col-actions">Actions</th>
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
                <span v-if="todo.description" class="todo-description">{{ truncate(todo.description, 60) }}</span>
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
              <td class="col-date">{{ formatDate(todo.created_at) }}</td>
              <td class="col-date">{{ todo.completed_at ? formatDate(todo.completed_at) : '-' }}</td>
              <td class="col-actions">
                <button class="btn-icon" @click="openEditModal(todo)" title="Edit description">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                    <path d="m15 5 4 4"/>
                  </svg>
                </button>
                <button class="btn-icon" @click="handleRestore(todo)" title="Restore to Open">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                    <path d="M3 3v5h5"/>
                  </svg>
                </button>
                <button class="btn-icon danger" @click="handleDelete(todo)" title="Delete permanently">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 6h18"/>
                    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                  </svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="hasMore" class="load-more">
        <button @click="loadMore" class="btn-secondary">
          Load More ({{ archivedTodos.length }} of {{ totalCount }})
        </button>
      </div>
    </div>

    <Modal :show="showEditModal" title="Edit Description" @close="closeEditModal">
      <form @submit.prevent="handleSaveEdit" class="edit-form">
        <div class="form-group">
          <label for="edit-title">Title</label>
          <input
            id="edit-title"
            :value="editingTodo?.title"
            type="text"
            class="form-input"
            disabled
          />
        </div>
        <div class="form-group">
          <label for="edit-description">Description</label>
          <textarea
            id="edit-description"
            v-model="editDescription"
            rows="5"
            placeholder="Enter description"
            class="form-input"
          ></textarea>
        </div>
        <div class="form-actions">
          <button type="button" @click="closeEditModal" class="btn-secondary">Cancel</button>
          <button type="submit" class="btn-primary">Save</button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTodoStore } from '@/stores/todoStore'
import Modal from '@/components/common/Modal.vue'

const todoStore = useTodoStore()

const archivedTodos = ref([])
const totalCount = ref(0)
const currentSkip = ref(0)
const limit = 50
const loading = ref(false)
const error = ref(null)

const showEditModal = ref(false)
const editingTodo = ref(null)
const editDescription = ref('')

const sortedTodos = computed(() => {
  return [...archivedTodos.value].sort((a, b) => {
    const dateA = new Date(a.created_at)
    const dateB = new Date(b.created_at)
    return dateB - dateA
  })
})

const completedCount = computed(() => {
  return archivedTodos.value.filter(t => t.status === 'Completed').length
})

const cancelledCount = computed(() => {
  return archivedTodos.value.filter(t => t.status === 'Cancelled').length
})

const hasMore = computed(() => {
  return archivedTodos.value.length < totalCount.value
})

onMounted(() => {
  loadArchived()
})

async function loadArchived() {
  loading.value = true
  error.value = null
  try {
    const response = await todoStore.fetchTodos({
      status: 'Completed,Cancelled',
      skip: 0,
      limit
    })
    archivedTodos.value = response.todos
    totalCount.value = response.total
    currentSkip.value = response.todos.length
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load archived todos'
    console.error('Failed to load archived todos:', err)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  try {
    const response = await todoStore.fetchTodos({
      status: 'Completed,Cancelled',
      skip: currentSkip.value,
      limit
    })
    archivedTodos.value = [...archivedTodos.value, ...response.todos]
    currentSkip.value = archivedTodos.value.length
  } catch (err) {
    console.error('Failed to load more todos:', err)
  }
}

async function handleRestore(todo) {
  if (confirm(`Restore "${todo.title}" to Open status?`)) {
    try {
      await todoStore.updateTodo(todo.id, { status: 'Open' })
      archivedTodos.value = archivedTodos.value.filter(t => t.id !== todo.id)
      totalCount.value--
    } catch (err) {
      console.error('Failed to restore todo:', err)
    }
  }
}

async function handleDelete(todo) {
  if (confirm(`Permanently delete "${todo.title}"? This cannot be undone.`)) {
    try {
      await todoStore.deleteTodo(todo.id)
      archivedTodos.value = archivedTodos.value.filter(t => t.id !== todo.id)
      totalCount.value--
    } catch (err) {
      console.error('Failed to delete todo:', err)
    }
  }
}

function openEditModal(todo) {
  editingTodo.value = todo
  editDescription.value = todo.description || ''
  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
  editingTodo.value = null
  editDescription.value = ''
}

async function handleSaveEdit() {
  if (!editingTodo.value) return
  
  try {
    await todoStore.updateTodo(editingTodo.value.id, { description: editDescription.value })
    const idx = archivedTodos.value.findIndex(t => t.id === editingTodo.value.id)
    if (idx !== -1) {
      archivedTodos.value[idx].description = editDescription.value
    }
    closeEditModal()
  } catch (err) {
    console.error('Failed to update description:', err)
  }
}

function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

function truncate(text, maxLength) {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}
</script>

<style scoped>
.archived-view {
  min-height: calc(100vh - 80px);
  background: #f9fafb;
  padding: 2rem;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  max-width: 1400px;
  margin-left: auto;
  margin-right: auto;
}

.view-header h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
}

.view-description {
  margin: 0;
  color: #6b7280;
  font-size: 1rem;
}

.header-stats {
  display: flex;
  gap: 0.75rem;
}

.stat-badge {
  padding: 0.375rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.stat-badge.completed {
  background: #dcfce7;
  color: #166534;
}

.stat-badge.cancelled {
  background: #fef2f2;
  color: #991b1b;
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

.archived-content {
  max-width: 1400px;
  margin: 0 auto;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 12px;
  border: 2px dashed #e5e7eb;
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

.todos-table td {
  padding: 0.875rem 1rem;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
}

.todos-table tbody tr:last-child td {
  border-bottom: none;
}

.todos-table tbody tr:hover {
  background: #f9fafb;
}

.todo-row.completed {
  background: #f0fdf4;
}

.todo-row.cancelled {
  background: #fefce8;
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

.col-actions {
  width: 120px;
  text-align: center;
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

.btn-icon {
  padding: 0.375rem;
  border: none;
  background: transparent;
  color: #6b7280;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-icon:hover {
  background: #f3f4f6;
  color: #111827;
}

.btn-icon.danger:hover {
  background: #fee2e2;
  color: #dc2626;
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

.btn-secondary:hover {
  background-color: #f9fafb;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.edit-form .form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.edit-form label {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.edit-form .form-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
  transition: all 0.2s;
}

.edit-form .form-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.edit-form .form-input:disabled {
  background-color: #f3f4f6;
  color: #6b7280;
  cursor: not-allowed;
}

.edit-form textarea.form-input {
  resize: vertical;
  font-family: inherit;
}

.edit-form .form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
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
  .archived-view {
    padding: 1rem;
  }

  .view-header {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>


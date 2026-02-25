<template>
  <div class="assets-view">
    <div class="view-header">
      <div>
        <h2>Assets</h2>
        <p class="view-description">
          Manage reusable assets like code, documents, and resources
        </p>
      </div>
      <div class="header-actions">
        <div class="header-stats" v-if="!loading && !error">
          <span class="stat-badge total">{{ items.length }} assets</span>
        </div>
        <button class="btn-primary" @click="openCreateModal">
          + New Asset
        </button>
      </div>
    </div>

    <div class="filters-bar">
      <div class="filter-group">
        <label>Project:</label>
        <select v-model="filterProjectId" @change="loadAssets">
          <option value="">All Projects</option>
          <option v-for="project in projects" :key="project.id" :value="project.id">
            {{ project.name }}
          </option>
        </select>
      </div>
      <div class="filter-group">
        <label>Task:</label>
        <select v-model="filterTodoId" @change="loadAssets">
          <option value="">All Tasks</option>
          <option v-for="todo in todos" :key="todo.id" :value="todo.id">
            {{ truncate(todo.title, 30) }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading assets...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadAssets" class="btn-primary">Retry</button>
    </div>

    <div v-else class="assets-content">
      <div v-if="items.length === 0" class="empty-state">
        <p>No assets found</p>
        <p class="empty-state-hint">
          Create your first asset to start building your library of reusable resources
        </p>
      </div>

      <div v-else class="table-container">
        <table class="assets-table">
          <thead>
            <tr>
              <th class="col-name">Name</th>
              <th class="col-description">Description</th>
              <th class="col-project">Project</th>
              <th class="col-todo">Task</th>
              <th class="col-url">Reference URL</th>
              <th class="col-reuse">Reuse Count</th>
              <th class="col-date">Created</th>
              <th class="col-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in sortedItems" :key="item.id" class="asset-row">
              <td class="col-name">
                <span class="asset-name">{{ item.name }}</span>
              </td>
              <td class="col-description">
                <span v-if="item.description" class="asset-description">{{ truncate(item.description, 50) }}</span>
                <span v-else class="no-value">-</span>
              </td>
              <td class="col-project">
                <span v-if="item.project_id" class="project-badge">
                  {{ getProjectName(item.project_id) }}
                </span>
                <span v-else class="no-value">-</span>
              </td>
              <td class="col-todo">
                <span v-if="item.todo_id" class="todo-badge">
                  {{ truncate(getTodoTitle(item.todo_id), 20) }}
                </span>
                <span v-else class="no-value">-</span>
              </td>
              <td class="col-url">
                <a 
                  v-if="item.reference_url"
                  :href="item.reference_url" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  class="url-link"
                  :title="item.reference_url"
                >
                  {{ truncate(item.reference_url, 35) }}
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                    <polyline points="15 3 21 3 21 9"/>
                    <line x1="10" x2="21" y1="14" y2="3"/>
                  </svg>
                </a>
                <span v-else class="no-value">-</span>
              </td>
              <td class="col-reuse">
                <span class="reuse-badge" :class="{ 'has-reuse': item.project_count > 0 }">
                  {{ item.project_count || 0 }}
                </span>
              </td>
              <td class="col-date">
                {{ formatDate(item.created_at) }}
              </td>
              <td class="col-actions">
                <button class="btn-icon" @click="openEditModal(item)" title="Edit">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                    <path d="m15 5 4 4"/>
                  </svg>
                </button>
                <button class="btn-icon danger" @click="handleDelete(item)" title="Delete">
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
          Load More ({{ items.length }} of {{ totalCount }})
        </button>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <Modal :show="showModal" :title="isEditing ? 'Edit Asset' : 'New Asset'" :wide="true" @close="closeModal">
      <form @submit.prevent="handleSubmit" class="asset-form">
        <div class="form-group">
          <label for="name">Name *</label>
          <input 
            id="name" 
            v-model="formData.name" 
            type="text" 
            required 
            placeholder="e.g., Flink SQL Helper Library"
          />
        </div>

        <div class="form-group">
          <label for="description">Description</label>
          <textarea 
            id="description" 
            v-model="formData.description" 
            rows="3"
            placeholder="Brief description of what this asset is and how it can be reused"
          ></textarea>
        </div>

        <div class="form-group">
          <label for="reference_url">Reference URL</label>
          <input 
            id="reference_url" 
            v-model="formData.reference_url" 
            type="url" 
            placeholder="https://github.com/org/repo or https://docs.example.com/resource"
          />
          <span class="form-hint">URL to the code repository, document, or resource</span>
        </div>

        <div class="form-group">
          <label for="project_id">Project</label>
          <select id="project_id" v-model="formData.project_id">
            <option :value="null">None</option>
            <option v-for="project in projects" :key="project.id" :value="project.id">
              {{ project.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="todo_id">Task</label>
          <select id="todo_id" v-model="formData.todo_id">
            <option :value="null">None</option>
            <option v-for="todo in todos" :key="todo.id" :value="todo.id">
              {{ truncate(todo.title, 40) }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="project_count">Reuse Count</label>
          <input 
            id="project_count" 
            v-model.number="formData.project_count" 
            type="number" 
            min="0"
            placeholder="0"
          />
          <span class="form-hint">Number of projects where this asset has been used</span>
        </div>
      </form>

      <template #footer>
        <button type="button" class="btn-secondary" @click="closeModal">Cancel</button>
        <button type="button" class="btn-primary" @click="handleSubmit" :disabled="!isFormValid">
          {{ isEditing ? 'Update' : 'Create' }}
        </button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAssetStore } from '@/stores/assetStore'
import Modal from '@/components/common/Modal.vue'

const store = useAssetStore()

const items = ref([])
const totalCount = ref(0)
const currentSkip = ref(0)
const limit = 50
const loading = ref(false)
const error = ref(null)

// Filters
const filterProjectId = ref('')
const filterTodoId = ref('')

// Modal state
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const formData = ref({
  name: '',
  description: '',
  reference_url: '',
  project_id: null,
  todo_id: null,
  project_count: 0
})

// Computed
const projects = computed(() => store.projects)
const todos = computed(() => store.todos)

const sortedItems = computed(() => {
  return [...items.value].sort((a, b) => {
    const dateA = new Date(a.created_at)
    const dateB = new Date(b.created_at)
    return dateB - dateA
  })
})

const hasMore = computed(() => {
  return items.value.length < totalCount.value
})

const isFormValid = computed(() => {
  return !!formData.value.name?.trim()
})

// Lifecycle
onMounted(async () => {
  await Promise.all([
    store.fetchProjects(),
    store.fetchTodos()
  ])
  await loadAssets()
})

// Methods
async function loadAssets() {
  loading.value = true
  error.value = null
  try {
    const params = { skip: 0, limit }
    if (filterProjectId.value) params.project_id = parseInt(filterProjectId.value)
    if (filterTodoId.value) params.todo_id = parseInt(filterTodoId.value)
    
    const response = await store.fetchItems(params)
    items.value = response.assets
    totalCount.value = response.total
    currentSkip.value = response.assets.length
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load assets'
    console.error('Failed to load assets:', err)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  try {
    const params = { skip: currentSkip.value, limit }
    if (filterProjectId.value) params.project_id = parseInt(filterProjectId.value)
    if (filterTodoId.value) params.todo_id = parseInt(filterTodoId.value)
    
    const response = await store.fetchItems(params)
    items.value = [...items.value, ...response.assets]
    currentSkip.value = items.value.length
  } catch (err) {
    console.error('Failed to load more items:', err)
  }
}

function getProjectName(projectId) {
  return store.getProjectName(projectId)
}

function getTodoTitle(todoId) {
  return store.getTodoTitle(todoId)
}

function openCreateModal() {
  isEditing.value = false
  editingId.value = null
  formData.value = {
    name: '',
    description: '',
    reference_url: '',
    project_id: null,
    todo_id: null,
    project_count: 0
  }
  showModal.value = true
}

function openEditModal(item) {
  isEditing.value = true
  editingId.value = item.id
  formData.value = {
    name: item.name,
    description: item.description || '',
    reference_url: item.reference_url,
    project_id: item.project_id,
    todo_id: item.todo_id,
    project_count: item.project_count || 0
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  isEditing.value = false
  editingId.value = null
}

async function handleSubmit() {
  if (!isFormValid.value) return
  
  try {
    if (isEditing.value) {
      const updated = await store.updateItem(editingId.value, formData.value)
      const index = items.value.findIndex(item => item.id === editingId.value)
      if (index !== -1) {
        items.value[index] = updated
      }
    } else {
      const created = await store.createItem(formData.value)
      items.value.unshift(created)
      totalCount.value++
    }
    closeModal()
  } catch (err) {
    console.error('Failed to save asset:', err)
    alert('Failed to save asset: ' + (err.response?.data?.detail || err.message))
  }
}

async function handleDelete(item) {
  if (confirm(`Delete asset "${item.name}"? This cannot be undone.`)) {
    try {
      await store.deleteItem(item.id)
      items.value = items.value.filter(i => i.id !== item.id)
      totalCount.value--
    } catch (err) {
      console.error('Failed to delete asset:', err)
      alert('Failed to delete asset: ' + (err.response?.data?.detail || err.message))
    }
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
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}
</script>

<style scoped>
.assets-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .assets-view {
  background: #0f172a;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.view-header h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
}

:global(.dark) .view-header h2 {
  color: #f1f5f9;
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

.stat-badge {
  padding: 0.375rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.stat-badge.total {
  background: #fce7f3;
  color: #be185d;
}

.filters-bar {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.filter-group select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  background: white;
  cursor: pointer;
  min-width: 150px;
}

.filter-group select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
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

.assets-content {
  width: 100%;
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
  width: 100%;
}

:global(.dark) .table-container {
  background: #1e293b;
  border-color: #334155;
}

.assets-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.assets-table th {
  background: #f9fafb;
  padding: 0.875rem 1rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}

:global(.dark) .assets-table th {
  background: #0f172a;
  color: #94a3b8;
  border-color: #334155;
}

.assets-table td {
  padding: 0.875rem 1rem;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
}

:global(.dark) .assets-table td {
  border-color: #334155;
}

.assets-table tbody tr:last-child td {
  border-bottom: none;
}

.assets-table tbody tr:hover {
  background: #f9fafb;
}

:global(.dark) .assets-table tbody tr:hover {
  background: #0f172a;
}

.col-name {
  width: 180px;
}

.col-description {
  min-width: 150px;
}

.col-project,
.col-todo {
  width: 140px;
}

.col-url {
  min-width: 200px;
}

.col-reuse {
  width: 90px;
  text-align: center;
}

.col-date {
  width: 100px;
  white-space: nowrap;
}

.col-actions {
  width: 80px;
  text-align: center;
}

.asset-name {
  display: block;
  font-weight: 600;
  color: #111827;
}

:global(.dark) .asset-name {
  color: #f1f5f9;
}

.asset-description {
  font-size: 0.8125rem;
  color: #6b7280;
}

.project-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: #d1fae5;
  color: #065f46;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.todo-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.url-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  color: #2563eb;
  text-decoration: none;
  font-size: 0.8125rem;
  font-family: ui-monospace, monospace;
}

.url-link:hover {
  text-decoration: underline;
}

.url-link svg {
  flex-shrink: 0;
  opacity: 0.6;
}

.reuse-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  padding: 0.25rem 0.5rem;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 9999px;
  font-size: 0.8125rem;
  font-weight: 600;
}

.reuse-badge.has-reuse {
  background: #fef3c7;
  color: #b45309;
}

:global(.dark) .reuse-badge {
  background: #374151;
  color: #9ca3af;
}

:global(.dark) .reuse-badge.has-reuse {
  background: #78350f;
  color: #fcd34d;
}

.no-value {
  color: #d1d5db;
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

.btn-primary:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background-color: #f9fafb;
}

/* Form styles */
.asset-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.form-group input,
.form-group textarea,
.form-group select {
  padding: 0.625rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9375rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-hint {
  font-size: 0.75rem;
  color: #6b7280;
}

@media (max-width: 1024px) {
  .table-container {
    overflow-x: auto;
  }
  
  .assets-table {
    min-width: 1000px;
  }
}

@media (max-width: 768px) {
  .assets-view {
    padding: 1rem;
  }

  .view-header {
    flex-direction: column;
    gap: 1rem;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .filters-bar {
    flex-direction: column;
    gap: 0.75rem;
  }

}
</style>


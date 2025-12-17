<template>
  <div class="projects-view">
    <div class="view-header">
      <div>
        <h2>Projects</h2>
        <p class="view-description">
          Manage customer projects and track their lifecycle
        </p>
      </div>
      <div class="header-actions">
        <div class="header-stats" v-if="!loading && !error">
          <span class="stat-badge active">{{ activeCount }} active</span>
          <span class="stat-badge draft">{{ draftCount }} draft</span>
        </div>
        <button class="btn-primary" @click="openCreateModal">
          + New Project
        </button>
      </div>
    </div>

    <div class="filters-bar">
      <div class="filter-group">
        <label>Customer:</label>
        <select v-model="filterCustomerId" @change="loadProjects">
          <option value="">All Customers</option>
          <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>Status:</label>
        <select v-model="filterStatus" @change="loadProjects">
          <option value="">All Statuses</option>
          <option value="Draft">Draft</option>
          <option value="Active">Active</option>
          <option value="On Hold">On Hold</option>
          <option value="Completed">Completed</option>
          <option value="Cancelled">Cancelled</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading projects...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadProjects" class="btn-primary">Retry</button>
    </div>

    <div v-else class="projects-content">
      <div v-if="projects.length === 0" class="empty-state">
        <p>No projects found</p>
        <p class="empty-state-hint">
          Create a project to start tracking customer work
        </p>
      </div>

      <div v-else class="projects-grid">
        <div 
          v-for="project in projects" 
          :key="project.id" 
          class="project-card"
          :class="[statusClass(project.status)]"
        >
          <div class="project-header">
            <span :class="['status-badge', statusClass(project.status)]">
              {{ project.status }}
            </span>
            <div class="project-actions">
              <button class="btn-icon" @click="openEditModal(project)" title="Edit">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                  <path d="m15 5 4 4"/>
                </svg>
              </button>
              <button class="btn-icon danger" @click="handleDelete(project)" title="Delete">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 6h18"/>
                  <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                  <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                </svg>
              </button>
            </div>
          </div>

          <h3 class="project-name">{{ project.name }}</h3>
          
          <p class="project-customer" v-if="getCustomerName(project.customer_id)">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            {{ getCustomerName(project.customer_id) }}
          </p>

          <p class="project-description" v-if="project.description">
            {{ truncate(project.description, 100) }}
          </p>

          <div class="project-tasks" v-if="project.tasks">
            <h4>Tasks</h4>
            <div class="tasks-preview" v-html="renderTasks(project.tasks)"></div>
          </div>

          <div class="project-meta">
            <span class="meta-item">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>
                <line x1="16" x2="16" y1="2" y2="6"/>
                <line x1="8" x2="8" y1="2" y2="6"/>
                <line x1="3" x2="21" y1="10" y2="10"/>
              </svg>
              {{ formatDate(project.created_at) }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="hasMore" class="load-more">
        <button @click="loadMore" class="btn-secondary">
          Load More ({{ projects.length }} of {{ totalCount }})
        </button>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <Modal :show="showModal" :title="isEditing ? 'Edit Project' : 'New Project'" @close="closeModal">
      <form @submit.prevent="handleSubmit" class="project-form">
        <div class="form-group">
          <label for="name">Project Name *</label>
          <input 
            id="name" 
            v-model="formData.name" 
            type="text" 
            required 
            placeholder="Enter project name"
          />
        </div>

        <div class="form-group">
          <label for="description">Description</label>
          <textarea 
            id="description" 
            v-model="formData.description" 
            rows="3"
            placeholder="Project description and goals"
          ></textarea>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="customer">Customer</label>
            <select id="customer" v-model="formData.customer_id">
              <option :value="null">No customer</option>
              <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>

          <div class="form-group">
            <label for="status">Status</label>
            <select id="status" v-model="formData.status">
              <option value="Draft">Draft</option>
              <option value="Active">Active</option>
              <option value="On Hold">On Hold</option>
              <option value="Completed">Completed</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label for="tasks">Tasks (Bullet List)</label>
          <textarea 
            id="tasks" 
            v-model="formData.tasks" 
            rows="5"
            placeholder="- Task 1&#10;- Task 2&#10;- Task 3"
            class="tasks-input"
          ></textarea>
          <span class="form-hint">Use markdown-style bullet points (- item)</span>
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
import { projectsApi, customersApi } from '@/services/api'
import Modal from '@/components/common/Modal.vue'

const projects = ref([])
const customers = ref([])
const totalCount = ref(0)
const currentSkip = ref(0)
const limit = 50
const loading = ref(false)
const error = ref(null)

// Filters
const filterCustomerId = ref('')
const filterStatus = ref('')

// Modal state
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const formData = ref({
  name: '',
  description: '',
  customer_id: null,
  status: 'Draft',
  tasks: ''
})

const activeCount = computed(() => {
  return projects.value.filter(p => p.status === 'Active').length
})

const draftCount = computed(() => {
  return projects.value.filter(p => p.status === 'Draft').length
})

const hasMore = computed(() => {
  return projects.value.length < totalCount.value
})

const isFormValid = computed(() => {
  return formData.value.name && formData.value.name.trim().length > 0
})

onMounted(async () => {
  await loadCustomers()
  await loadProjects()
})

async function loadCustomers() {
  try {
    const response = await customersApi.list({ limit: 500 })
    customers.value = response.data.customers
  } catch (err) {
    console.error('Failed to load customers:', err)
  }
}

async function loadProjects() {
  loading.value = true
  error.value = null
  try {
    const params = { skip: 0, limit }
    if (filterCustomerId.value) params.customer_id = filterCustomerId.value
    if (filterStatus.value) params.status = filterStatus.value
    
    const response = await projectsApi.list(params)
    projects.value = response.data.projects
    totalCount.value = response.data.total
    currentSkip.value = response.data.projects.length
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load projects'
    console.error('Failed to load projects:', err)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  try {
    const params = { skip: currentSkip.value, limit }
    if (filterCustomerId.value) params.customer_id = filterCustomerId.value
    if (filterStatus.value) params.status = filterStatus.value
    
    const response = await projectsApi.list(params)
    projects.value = [...projects.value, ...response.data.projects]
    currentSkip.value = projects.value.length
  } catch (err) {
    console.error('Failed to load more projects:', err)
  }
}

function getCustomerName(customerId) {
  if (!customerId) return null
  const customer = customers.value.find(c => c.id === customerId)
  return customer?.name || null
}

function openCreateModal() {
  isEditing.value = false
  editingId.value = null
  formData.value = {
    name: '',
    description: '',
    customer_id: null,
    status: 'Draft',
    tasks: ''
  }
  showModal.value = true
}

function openEditModal(project) {
  isEditing.value = true
  editingId.value = project.id
  formData.value = {
    name: project.name,
    description: project.description || '',
    customer_id: project.customer_id || null,
    status: project.status,
    tasks: project.tasks || ''
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
    const payload = { ...formData.value }
    // Don't send null customer_id as it can cause issues
    if (payload.customer_id === null) {
      delete payload.customer_id
    }
    
    if (isEditing.value) {
      const response = await projectsApi.update(editingId.value, payload)
      const index = projects.value.findIndex(p => p.id === editingId.value)
      if (index !== -1) {
        projects.value[index] = response.data
      }
    } else {
      const response = await projectsApi.create(payload)
      projects.value.unshift(response.data)
      totalCount.value++
    }
    closeModal()
  } catch (err) {
    console.error('Failed to save project:', err)
    alert(err.response?.data?.detail || 'Failed to save project')
  }
}

async function handleDelete(project) {
  if (confirm(`Delete project "${project.name}"? This cannot be undone.`)) {
    try {
      await projectsApi.delete(project.id)
      projects.value = projects.value.filter(p => p.id !== project.id)
      totalCount.value--
    } catch (err) {
      console.error('Failed to delete project:', err)
      alert(err.response?.data?.detail || 'Failed to delete project')
    }
  }
}

function statusClass(status) {
  return status.toLowerCase().replace(' ', '-')
}

function renderTasks(tasks) {
  if (!tasks) return ''
  // Convert markdown-style bullets to HTML list
  const lines = tasks.split('\n').filter(line => line.trim())
  const items = lines.map(line => {
    const text = line.replace(/^[-*]\s*/, '').trim()
    return text ? `<li>${escapeHtml(text)}</li>` : ''
  }).filter(Boolean)
  return items.length ? `<ul>${items.join('')}</ul>` : ''
}

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
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
.projects-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .projects-view {
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

.stat-badge.active {
  background: #dcfce7;
  color: #166534;
}

.stat-badge.draft {
  background: #f3f4f6;
  color: #374151;
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

:global(.dark) .filter-group label {
  color: #94a3b8;
}

.filter-group select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  background: white;
  cursor: pointer;
}

:global(.dark) .filter-group select {
  background: #1e293b;
  border-color: #334155;
  color: #f1f5f9;
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

.projects-content {
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

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 1.25rem;
}

.project-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 1.25rem;
  transition: all 0.2s;
}

:global(.dark) .project-card {
  background: #1e293b;
  border-color: #334155;
}

.project-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.project-card.completed {
  border-left: 4px solid #10b981;
}

.project-card.active {
  border-left: 4px solid #3b82f6;
}

.project-card.draft {
  border-left: 4px solid #9ca3af;
}

.project-card.on-hold {
  border-left: 4px solid #f59e0b;
}

.project-card.cancelled {
  border-left: 4px solid #ef4444;
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.status-badge.completed {
  background: #dcfce7;
  color: #166534;
}

.status-badge.active {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.draft {
  background: #f3f4f6;
  color: #374151;
}

.status-badge.on-hold {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.cancelled {
  background: #fee2e2;
  color: #991b1b;
}

.project-actions {
  display: flex;
  gap: 0.25rem;
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

:global(.dark) .btn-icon:hover {
  background: #334155;
  color: #f1f5f9;
}

.btn-icon.danger:hover {
  background: #fee2e2;
  color: #dc2626;
}

.project-name {
  margin: 0 0 0.5rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
}

:global(.dark) .project-name {
  color: #f1f5f9;
}

.project-customer {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  color: #6b7280;
}

.project-customer svg {
  color: #9ca3af;
}

.project-description {
  margin: 0 0 1rem 0;
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.5;
}

.project-tasks {
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 8px;
}

:global(.dark) .project-tasks {
  background: #0f172a;
}

.project-tasks h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6b7280;
}

.tasks-preview {
  font-size: 0.8125rem;
  color: #374151;
}

:global(.dark) .tasks-preview {
  color: #94a3b8;
}

.tasks-preview :deep(ul) {
  margin: 0;
  padding-left: 1.25rem;
}

.tasks-preview :deep(li) {
  margin-bottom: 0.25rem;
}

.project-meta {
  display: flex;
  gap: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid #f3f4f6;
}

:global(.dark) .project-meta {
  border-top-color: #334155;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  color: #9ca3af;
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

/* Form styles */
.project-form {
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

:global(.dark) .form-group label {
  color: #94a3b8;
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

:global(.dark) .form-group input,
:global(.dark) .form-group textarea,
:global(.dark) .form-group select {
  background: #1e293b;
  border-color: #334155;
  color: #f1f5f9;
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

.tasks-input {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.875rem !important;
  line-height: 1.6;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-hint {
  font-size: 0.75rem;
  color: #6b7280;
}

@media (max-width: 768px) {
  .projects-view {
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

  .projects-grid {
    grid-template-columns: 1fr;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>



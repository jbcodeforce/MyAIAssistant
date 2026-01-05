<template>
  <div class="projects-view">
    <div class="view-header">
      <div>
        <h2>Projects</h2>
        <p class="view-description">
          Manage organization projects and track their lifecycle
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
        <label>Organization:</label>
        <select v-model="filterOrganizationId" @change="loadProjects">
          <option value="">All Organizations</option>
          <option v-for="o in organizations" :key="o.id" :value="o.id">{{ o.name }}</option>
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
          Create a project to start tracking organization work
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
          
          <p class="project-organization" v-if="getOrganizationName(project.organization_id)">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            {{ getOrganizationName(project.organization_id) }}
          </p>

          <div class="project-sections">
            <div 
              v-if="project.description" 
              class="section-chip"
              @click="openSectionViewer(project, 'description')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              Description
            </div>

            <div 
              v-if="project.tasks" 
              class="section-chip"
              @click="openSectionViewer(project, 'tasks')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 11l3 3L22 4"/>
                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
              </svg>
              Tasks
            </div>
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
            <router-link :to="`/projects/${project.id}/todos`" class="view-tasks-link">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 11l3 3L22 4"/>
                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
              </svg>
              View Todos
            </router-link>
          </div>
        </div>
      </div>

      <div v-if="hasMore" class="load-more">
        <button @click="loadMore" class="btn-secondary">
          Load More ({{ projects.length }} of {{ totalCount }})
        </button>
      </div>
    </div>

    <!-- Section Viewer Modal -->
    <Modal 
      :show="showSectionViewer" 
      :title="sectionViewerTitle" 
      size="fullscreen" 
      @close="closeSectionViewer"
    >
      <div class="section-viewer-content">
        <div class="markdown-preview view-mode" v-html="renderedSectionContent"></div>
      </div>
      <template #footer>
        <button type="button" class="btn-secondary" @click="closeSectionViewer">Close</button>
        <button type="button" class="btn-primary" @click="editFromViewer">Edit</button>
      </template>
    </Modal>

    <!-- Create/Edit Modal -->
    <Modal :show="showModal" :title="isEditing ? 'Edit Project' : 'New Project'" @close="closeModal" size="fullscreen">
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

        <div class="form-row">
          <div class="form-group">
            <label for="organization">Organization</label>
            <select id="organization" v-model="formData.organization_id">
              <option :value="null">No organization</option>
              <option v-for="o in organizations" :key="o.id" :value="o.id">{{ o.name }}</option>
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
          <label>Description</label>
          <div class="markdown-editor-container">
            <div class="editor-tabs">
              <button 
                type="button" 
                :class="['tab-btn', { active: descriptionTab === 'write' }]"
                @click="descriptionTab = 'write'"
              >
                Write
              </button>
              <button 
                type="button" 
                :class="['tab-btn', { active: descriptionTab === 'preview' }]"
                @click="descriptionTab = 'preview'"
              >
                Preview
              </button>
            </div>
            <textarea 
              v-if="descriptionTab === 'write'"
              v-model="formData.description" 
              class="markdown-textarea"
              rows="8"
              placeholder="## Project Overview

Describe the project goals, scope, and key deliverables.

### Objectives
- Objective 1
- Objective 2

### Timeline
- **Phase 1**: Discovery (2 weeks)
- **Phase 2**: Implementation (4 weeks)"
            ></textarea>
            <div v-else class="markdown-preview" v-html="renderedDescription"></div>
          </div>
          <span class="form-hint">Project description and goals (supports Markdown)</span>
        </div>

        <div class="form-group">
          <label>Tasks</label>
          <div class="markdown-editor-container">
            <div class="editor-tabs">
              <button 
                type="button" 
                :class="['tab-btn', { active: tasksTab === 'write' }]"
                @click="tasksTab = 'write'"
              >
                Write
              </button>
              <button 
                type="button" 
                :class="['tab-btn', { active: tasksTab === 'preview' }]"
                @click="tasksTab = 'preview'"
              >
                Preview
              </button>
            </div>
            <textarea 
              v-if="tasksTab === 'write'"
              v-model="formData.tasks" 
              class="markdown-textarea"
              rows="8"
              placeholder="## Current Tasks

### In Progress
- [ ] Task 1 - assignee
- [ ] Task 2 - assignee

### Completed
- [x] Initial setup
- [x] Requirements gathering"
            ></textarea>
            <div v-else class="markdown-preview" v-html="renderedTasks"></div>
          </div>
          <span class="form-hint">Project tasks and action items (supports Markdown)</span>
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { projectsApi, organizationsApi } from '@/services/api'
import Modal from '@/components/common/Modal.vue'

const route = useRoute()

const projects = ref([])
const organizations = ref([])
const totalCount = ref(0)
const currentSkip = ref(0)
const limit = 50
const loading = ref(false)
const error = ref(null)

// Filters
const filterOrganizationId = ref('')
const filterStatus = ref('')

// Modal state
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const formData = ref({
  name: '',
  description: '',
  organization_id: null,
  status: 'Draft',
  tasks: ''
})

// Editor tabs
const descriptionTab = ref('write')
const tasksTab = ref('write')

// Section viewer modal state
const showSectionViewer = ref(false)
const viewingProject = ref(null)
const viewingSection = ref('')

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

// Rendered markdown for form fields
const renderedDescription = computed(() => marked(formData.value.description || ''))
const renderedTasks = computed(() => marked(formData.value.tasks || ''))

// Section viewer computeds
const sectionLabels = {
  description: 'Description',
  tasks: 'Tasks'
}

const sectionViewerTitle = computed(() => {
  if (!viewingProject.value) return ''
  return `${viewingProject.value.name} - ${sectionLabels[viewingSection.value] || ''}`
})

const renderedSectionContent = computed(() => {
  if (!viewingProject.value || !viewingSection.value) return ''
  const content = viewingProject.value[viewingSection.value] || ''
  return marked(content)
})

onMounted(async () => {
  await loadOrganizations()
  
  // Check for organization query parameter
  if (route.query.organization) {
    filterOrganizationId.value = route.query.organization
  }
  
  await loadProjects()
})

// Watch for route query changes
watch(
  () => route.query.organization,
  (newOrgId) => {
    if (newOrgId !== undefined) {
      filterOrganizationId.value = newOrgId || ''
      loadProjects()
    }
  }
)

async function loadOrganizations() {
  try {
    const response = await organizationsApi.list({ limit: 500 })
    organizations.value = response.data.organizations
  } catch (err) {
    console.error('Failed to load organizations:', err)
  }
}

async function loadProjects() {
  loading.value = true
  error.value = null
  try {
    const params = { skip: 0, limit }
    if (filterOrganizationId.value) params.organization_id = filterOrganizationId.value
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
    if (filterOrganizationId.value) params.organization_id = filterOrganizationId.value
    if (filterStatus.value) params.status = filterStatus.value
    
    const response = await projectsApi.list(params)
    projects.value = [...projects.value, ...response.data.projects]
    currentSkip.value = projects.value.length
  } catch (err) {
    console.error('Failed to load more projects:', err)
  }
}

function getOrganizationName(organizationId) {
  if (!organizationId) return null
  const organization = organizations.value.find(o => o.id === organizationId)
  return organization?.name || null
}

function openCreateModal() {
  isEditing.value = false
  editingId.value = null
  formData.value = {
    name: '',
    description: '',
    organization_id: null,
    status: 'Draft',
    tasks: ''
  }
  resetTabs()
  showModal.value = true
}

function openEditModal(project) {
  isEditing.value = true
  editingId.value = project.id
  formData.value = {
    name: project.name,
    description: project.description || '',
    organization_id: project.organization_id || null,
    status: project.status,
    tasks: project.tasks || ''
  }
  resetTabs()
  showModal.value = true
}

function resetTabs() {
  descriptionTab.value = 'write'
  tasksTab.value = 'write'
}

function closeModal() {
  showModal.value = false
  isEditing.value = false
  editingId.value = null
}

function openSectionViewer(project, section) {
  viewingProject.value = project
  viewingSection.value = section
  showSectionViewer.value = true
}

function closeSectionViewer() {
  showSectionViewer.value = false
  viewingProject.value = null
  viewingSection.value = ''
}

function editFromViewer() {
  const project = viewingProject.value
  closeSectionViewer()
  if (project) {
    openEditModal(project)
  }
}

async function handleSubmit() {
  if (!isFormValid.value) return
  
  try {
    const payload = { ...formData.value }
    // Don't send null organization_id as it can cause issues
    if (payload.organization_id === null) {
      delete payload.organization_id
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

function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
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
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.project-card {
  background: white;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  padding: 1rem;
  transition: all 0.2s;
}

:global(.dark) .project-card {
  background: #1e293b;
  border-color: #334155;
}

.project-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
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
  margin-bottom: 0.5rem;
}

.status-badge {
  display: inline-block;
  padding: 0.1875rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.625rem;
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
  gap: 0.125rem;
}

.btn-icon {
  padding: 0.25rem;
  border: none;
  background: transparent;
  color: #9ca3af;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-icon:hover {
  background: #f3f4f6;
  color: #374151;
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
  margin: 0 0 0.375rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

:global(.dark) .project-name {
  color: #f1f5f9;
}

.project-organization {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin: 0 0 0.625rem 0;
  font-size: 0.75rem;
  color: #6b7280;
}

.project-organization svg {
  color: #9ca3af;
  width: 12px;
  height: 12px;
}

.project-sections {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-bottom: 0.75rem;
}

.section-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 0.6875rem;
  font-weight: 500;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.15s;
}

.section-chip:hover {
  background: #dbeafe;
  color: #1e40af;
}

:global(.dark) .section-chip {
  background: #334155;
  color: #94a3b8;
}

:global(.dark) .section-chip:hover {
  background: #1e3a5f;
  color: #60a5fa;
}

.section-chip svg {
  opacity: 0.7;
}

.project-meta {
  display: flex;
  gap: 0.75rem;
  padding-top: 0.625rem;
  border-top: 1px solid #f3f4f6;
}

:global(.dark) .project-meta {
  border-top-color: #334155;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.6875rem;
  color: #9ca3af;
}

.meta-item svg {
  width: 12px;
  height: 12px;
}

.view-tasks-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  margin-left: auto;
  padding: 0.25rem 0.5rem;
  font-size: 0.6875rem;
  font-weight: 500;
  color: #2563eb;
  text-decoration: none;
  background: #eff6ff;
  border-radius: 4px;
  transition: all 0.15s;
}

.view-tasks-link:hover {
  background: #dbeafe;
  color: #1d4ed8;
}

:global(.dark) .view-tasks-link {
  background: rgba(37, 99, 235, 0.15);
  color: #60a5fa;
}

:global(.dark) .view-tasks-link:hover {
  background: rgba(37, 99, 235, 0.25);
  color: #93c5fd;
}

.view-tasks-link svg {
  width: 12px;
  height: 12px;
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

/* Section Viewer */
.section-viewer-content {
  min-height: 200px;
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
.form-group select {
  padding: 0.625rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9375rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}

:global(.dark) .form-group input,
:global(.dark) .form-group select {
  background: #1e293b;
  border-color: #334155;
  color: #f1f5f9;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
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

/* Markdown Editor */
.markdown-editor-container {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  overflow: hidden;
}

:global(.dark) .markdown-editor-container {
  border-color: #334155;
}

.editor-tabs {
  display: flex;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

:global(.dark) .editor-tabs {
  background: #0f172a;
  border-bottom-color: #334155;
}

.tab-btn {
  padding: 0.5rem 0.875rem;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border-bottom: 2px solid transparent;
}

.tab-btn:hover {
  color: #374151;
  background: rgba(0, 0, 0, 0.02);
}

:global(.dark) .tab-btn:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.02);
}

.tab-btn.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
  background: white;
}

:global(.dark) .tab-btn.active {
  background: #1e293b;
  color: #60a5fa;
}

.markdown-textarea {
  width: 100%;
  padding: 0.75rem;
  border: none;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.8125rem;
  line-height: 1.6;
  resize: vertical;
  min-height: 150px;
  background: white;
}

:global(.dark) .markdown-textarea {
  background: #1e293b;
  color: #f1f5f9;
}

.markdown-textarea:focus {
  outline: none;
}

.markdown-textarea::placeholder {
  color: #9ca3af;
}

.markdown-preview {
  padding: 0.75rem;
  min-height: 150px;
  max-height: 400px;
  overflow-y: auto;
  background: white;
  line-height: 1.6;
  font-size: 0.875rem;
}

:global(.dark) .markdown-preview {
  background: #1e293b;
  color: #f1f5f9;
}

.markdown-preview.view-mode {
  min-height: 200px;
  max-height: 600px;
}

.markdown-preview :deep(h1) {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.75rem 0;
  padding-bottom: 0.375rem;
  border-bottom: 1px solid #e5e7eb;
}

:global(.dark) .markdown-preview :deep(h1) {
  border-bottom-color: #334155;
}

.markdown-preview :deep(h2) {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 1rem 0 0.5rem 0;
  color: #1e40af;
}

:global(.dark) .markdown-preview :deep(h2) {
  color: #60a5fa;
}

.markdown-preview :deep(h3) {
  font-size: 1rem;
  font-weight: 600;
  margin: 0.75rem 0 0.375rem 0;
}

.markdown-preview :deep(p) {
  margin: 0 0 0.5rem 0;
}

.markdown-preview :deep(ul),
.markdown-preview :deep(ol) {
  padding-left: 1.25rem;
  margin: 0 0 0.75rem 0;
}

.markdown-preview :deep(li) {
  margin: 0.125rem 0;
}

.markdown-preview :deep(strong) {
  font-weight: 600;
}

.markdown-preview :deep(code) {
  background: #f3f4f6;
  padding: 0.125rem 0.25rem;
  border-radius: 3px;
  font-family: ui-monospace, monospace;
  font-size: 0.8125em;
}

:global(.dark) .markdown-preview :deep(code) {
  background: #334155;
}

.markdown-preview :deep(pre) {
  background: #1f2937;
  color: #f9fafb;
  padding: 0.75rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.75rem 0;
}

.markdown-preview :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

.markdown-preview :deep(blockquote) {
  border-left: 3px solid #2563eb;
  padding-left: 0.75rem;
  margin: 0.75rem 0;
  color: #4b5563;
  font-style: italic;
}

:global(.dark) .markdown-preview :deep(blockquote) {
  color: #94a3b8;
}

.markdown-preview :deep(input[type="checkbox"]) {
  margin-right: 0.375rem;
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

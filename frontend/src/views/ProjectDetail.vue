<template>
  <div class="project-detail-view">
    <div class="view-header">
      <div class="header-left">
        <router-link to="/projects" class="back-link">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
          Back to Projects
        </router-link>
        <h2 v-if="project">{{ project.name }}</h2>
        <h2 v-else-if="loading">Loading...</h2>
      </div>
      <div class="header-actions" v-if="project">
        <button class="btn-secondary" @click="editProject">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
            <path d="m15 5 4 4"/>
          </svg>
          Edit
        </button>
        <router-link 
          :to="`/projects/${project.id}/todos`" 
          class="btn-primary"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 11l3 3L22 4"/>
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
          </svg>
          View Todos
        </router-link>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading project...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadProject" class="btn-primary">Retry</button>
    </div>

    <div v-else-if="project" class="project-content">
      <div class="project-meta">
        <span :class="['status-badge', statusClass(project.status)]">
          {{ project.status }}
        </span>
        <router-link 
          v-if="organizationName"
          :to="`/organizations/${project.organization_id}`"
          class="meta-link"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          {{ organizationName }}
        </router-link>
        <div class="meta-item">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>
            <line x1="16" x2="16" y1="2" y2="6"/>
            <line x1="8" x2="8" y1="2" y2="6"/>
            <line x1="3" x2="21" y1="10" y2="10"/>
          </svg>
          Created {{ formatDate(project.created_at) }}
        </div>
        <div class="meta-item" v-if="project.updated_at !== project.created_at">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/>
            <path d="M21 3v5h-5"/>
          </svg>
          Updated {{ formatDate(project.updated_at) }}
        </div>
      </div>

      <div class="sections-grid">
        <div class="section-card full-width" v-if="project.description">
          <div class="section-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <h3>Description</h3>
          </div>
          <div class="section-content markdown-preview" v-html="renderedDescription"></div>
        </div>

        <div class="section-card full-width" v-if="project.tasks">
          <div class="section-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 11l3 3L22 4"/>
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
            </svg>
            <h3>Tasks</h3>
          </div>
          <div class="section-content markdown-preview" v-html="renderedTasks"></div>
        </div>

        <div class="section-card" v-if="project.past_steps">
          <div class="section-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
              <path d="M3 3v5h5"/>
            </svg>
            <h3>Past Steps</h3>
          </div>
          <div class="section-content markdown-preview" v-html="renderedPastSteps"></div>
        </div>

        <div class="section-card" v-if="project.next_steps">
          <div class="section-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14"/>
              <path d="m12 5 7 7-7 7"/>
            </svg>
            <h3>Next Steps</h3>
          </div>
          <div class="section-content markdown-preview" v-html="renderedNextSteps"></div>
        </div>
      </div>

      <div class="empty-content" v-if="!hasContent">
        <p>No content has been added to this project yet.</p>
        <button class="btn-primary" @click="editProject">Add Content</button>
      </div>
    </div>

    <!-- Edit Modal -->
    <Modal 
      :show="showEditModal" 
      title="Edit Project" 
      size="fullscreen" 
      @close="closeEditModal"
    >
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
              rows="6"
              placeholder="## Project Overview

Describe the project goals, scope, and key deliverables."
            ></textarea>
            <div v-else class="markdown-preview form-preview" v-html="formRenderedDescription"></div>
          </div>
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
              rows="6"
              placeholder="## Current Tasks

- [ ] Task 1
- [ ] Task 2"
            ></textarea>
            <div v-else class="markdown-preview form-preview" v-html="formRenderedTasks"></div>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Past Steps</label>
            <div class="markdown-editor-container">
              <div class="editor-tabs">
                <button 
                  type="button" 
                  :class="['tab-btn', { active: pastStepsTab === 'write' }]"
                  @click="pastStepsTab = 'write'"
                >
                  Write
                </button>
                <button 
                  type="button" 
                  :class="['tab-btn', { active: pastStepsTab === 'preview' }]"
                  @click="pastStepsTab = 'preview'"
                >
                  Preview
                </button>
              </div>
              <textarea 
                v-if="pastStepsTab === 'write'"
                v-model="formData.past_steps" 
                class="markdown-textarea"
                rows="5"
                placeholder="- Completed initial analysis
- Met with stakeholders"
              ></textarea>
              <div v-else class="markdown-preview form-preview" v-html="formRenderedPastSteps"></div>
            </div>
          </div>

          <div class="form-group">
            <label>Next Steps</label>
            <div class="markdown-editor-container">
              <div class="editor-tabs">
                <button 
                  type="button" 
                  :class="['tab-btn', { active: nextStepsTab === 'write' }]"
                  @click="nextStepsTab = 'write'"
                >
                  Write
                </button>
                <button 
                  type="button" 
                  :class="['tab-btn', { active: nextStepsTab === 'preview' }]"
                  @click="nextStepsTab = 'preview'"
                >
                  Preview
                </button>
              </div>
              <textarea 
                v-if="nextStepsTab === 'write'"
                v-model="formData.next_steps" 
                class="markdown-textarea"
                rows="5"
                placeholder="- Finalize design
- Begin implementation"
              ></textarea>
              <div v-else class="markdown-preview form-preview" v-html="formRenderedNextSteps"></div>
            </div>
          </div>
        </div>
      </form>

      <template #footer>
        <button type="button" class="btn-secondary" @click="closeEditModal">Cancel</button>
        <button type="button" class="btn-primary" @click="handleSubmit" :disabled="!isFormValid">
          Update
        </button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import { projectsApi, organizationsApi } from '@/services/api'
import Modal from '@/components/common/Modal.vue'

const route = useRoute()
const router = useRouter()

const project = ref(null)
const organizations = ref([])
const loading = ref(false)
const error = ref(null)

// Edit modal state
const showEditModal = ref(false)
const formData = ref({
  name: '',
  description: '',
  organization_id: null,
  status: 'Draft',
  tasks: '',
  past_steps: '',
  next_steps: ''
})

// Editor tabs
const descriptionTab = ref('write')
const tasksTab = ref('write')
const pastStepsTab = ref('write')
const nextStepsTab = ref('write')

// Computed for rendered markdown (view mode)
const renderedDescription = computed(() => marked(project.value?.description || ''))
const renderedTasks = computed(() => marked(project.value?.tasks || ''))
const renderedPastSteps = computed(() => marked(project.value?.past_steps || ''))
const renderedNextSteps = computed(() => marked(project.value?.next_steps || ''))

// Computed for form rendered markdown
const formRenderedDescription = computed(() => marked(formData.value.description || ''))
const formRenderedTasks = computed(() => marked(formData.value.tasks || ''))
const formRenderedPastSteps = computed(() => marked(formData.value.past_steps || ''))
const formRenderedNextSteps = computed(() => marked(formData.value.next_steps || ''))

const organizationName = computed(() => {
  if (!project.value?.organization_id) return null
  const org = organizations.value.find(o => o.id === project.value.organization_id)
  return org?.name || null
})

const hasContent = computed(() => {
  if (!project.value) return false
  return project.value.description || 
         project.value.tasks || 
         project.value.past_steps || 
         project.value.next_steps
})

const isFormValid = computed(() => {
  return formData.value.name && formData.value.name.trim().length > 0
})

onMounted(async () => {
  await Promise.all([loadProject(), loadOrganizations()])
})

async function loadProject() {
  const id = route.params.id
  if (!id) {
    error.value = 'Project ID not provided'
    return
  }

  loading.value = true
  error.value = null
  try {
    const response = await projectsApi.get(id)
    project.value = response.data
  } catch (err) {
    if (err.response?.status === 404) {
      error.value = 'Project not found'
    } else {
      error.value = err.response?.data?.detail || 'Failed to load project'
    }
    console.error('Failed to load project:', err)
  } finally {
    loading.value = false
  }
}

async function loadOrganizations() {
  try {
    const response = await organizationsApi.list({ limit: 500 })
    organizations.value = response.data.organizations
  } catch (err) {
    console.error('Failed to load organizations:', err)
  }
}

function editProject() {
  formData.value = {
    name: project.value.name,
    description: project.value.description || '',
    organization_id: project.value.organization_id || null,
    status: project.value.status,
    tasks: project.value.tasks || '',
    past_steps: project.value.past_steps || '',
    next_steps: project.value.next_steps || ''
  }
  resetTabs()
  showEditModal.value = true
}

function resetTabs() {
  descriptionTab.value = 'write'
  tasksTab.value = 'write'
  pastStepsTab.value = 'write'
  nextStepsTab.value = 'write'
}

function closeEditModal() {
  showEditModal.value = false
}

async function handleSubmit() {
  if (!isFormValid.value) return
  
  try {
    const payload = { ...formData.value }
    if (payload.organization_id === null) {
      delete payload.organization_id
    }
    
    const response = await projectsApi.update(project.value.id, payload)
    project.value = response.data
    closeEditModal()
  } catch (err) {
    console.error('Failed to update project:', err)
    alert(err.response?.data?.detail || 'Failed to update project')
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
.project-detail-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .project-detail-view {
  background: #0f172a;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
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

.view-header h2 {
  margin: 0;
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
}

:global(.dark) .view-header h2 {
  color: #f1f5f9;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.project-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.875rem;
  color: #6b7280;
}

:global(.dark) .meta-item {
  color: #94a3b8;
}

.meta-item svg {
  color: #9ca3af;
}

.meta-link {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.875rem;
  color: #6b7280;
  text-decoration: none;
  transition: color 0.15s;
}

.meta-link:hover {
  color: #2563eb;
}

:global(.dark) .meta-link {
  color: #94a3b8;
}

:global(.dark) .meta-link:hover {
  color: #60a5fa;
}

.meta-link svg {
  color: #9ca3af;
}

.meta-link:hover svg {
  color: #2563eb;
}

:global(.dark) .meta-link:hover svg {
  color: #60a5fa;
}

/* Status badges */
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
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

.project-content {
  width: 100%;
}

.sections-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.section-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

:global(.dark) .section-card {
  background: #1e293b;
  border-color: #334155;
}

.section-card.full-width {
  grid-column: 1 / -1;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 1.25rem;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

:global(.dark) .section-header {
  background: #0f172a;
  border-bottom-color: #334155;
}

.section-header svg {
  color: #6366f1;
}

.section-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

:global(.dark) .section-header h3 {
  color: #f1f5f9;
}

.section-content {
  padding: 1.25rem;
}

.empty-content {
  text-align: center;
  padding: 3rem 2rem;
  background: white;
  border-radius: 12px;
  border: 2px dashed #e5e7eb;
}

:global(.dark) .empty-content {
  background: #1e293b;
  border-color: #334155;
}

.empty-content p {
  margin: 0 0 1rem 0;
  color: #6b7280;
}

/* Buttons */
.btn-primary,
.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  text-decoration: none;
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

/* Markdown Preview */
.markdown-preview {
  line-height: 1.6;
  font-size: 0.9375rem;
  color: #374151;
}

:global(.dark) .markdown-preview {
  color: #e2e8f0;
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
  font-size: 1.25rem;
  font-weight: 600;
  margin: 1.25rem 0 0.625rem 0;
  color: #1e40af;
}

:global(.dark) .markdown-preview :deep(h2) {
  color: #60a5fa;
}

.markdown-preview :deep(h3) {
  font-size: 1.0625rem;
  font-weight: 600;
  margin: 1rem 0 0.5rem 0;
}

.markdown-preview :deep(p) {
  margin: 0 0 0.75rem 0;
}

.markdown-preview :deep(ul),
.markdown-preview :deep(ol) {
  padding-left: 1.5rem;
  margin: 0 0 1rem 0;
}

.markdown-preview :deep(li) {
  margin: 0.25rem 0;
}

.markdown-preview :deep(strong) {
  font-weight: 600;
}

.markdown-preview :deep(code) {
  background: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: ui-monospace, monospace;
  font-size: 0.875em;
}

:global(.dark) .markdown-preview :deep(code) {
  background: #334155;
}

.markdown-preview :deep(pre) {
  background: #1f2937;
  color: #f9fafb;
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1rem 0;
}

.markdown-preview :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

.markdown-preview :deep(blockquote) {
  border-left: 4px solid #2563eb;
  padding-left: 1rem;
  margin: 1rem 0;
  color: #4b5563;
  font-style: italic;
}

:global(.dark) .markdown-preview :deep(blockquote) {
  color: #94a3b8;
}

.markdown-preview :deep(input[type="checkbox"]) {
  margin-right: 0.375rem;
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
  min-height: 100px;
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

.markdown-preview.form-preview {
  padding: 0.75rem;
  min-height: 100px;
  max-height: 300px;
  overflow-y: auto;
  background: white;
}

:global(.dark) .markdown-preview.form-preview {
  background: #1e293b;
}

@media (max-width: 768px) {
  .project-detail-view {
    padding: 1rem;
  }

  .view-header {
    flex-direction: column;
    gap: 1rem;
  }

  .header-actions {
    width: 100%;
  }

  .project-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .sections-grid {
    grid-template-columns: 1fr;
  }

  .section-card.full-width {
    grid-column: 1;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>


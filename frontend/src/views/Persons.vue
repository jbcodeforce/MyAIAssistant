<template>
  <div class="persons-view">
    <div class="view-header">
      <div>
        <h2>Persons</h2>
        <p class="view-description">
          Track interactions with people during tasks and projects
        </p>
      </div>
      <div class="header-actions">
        <span class="person-count" v-if="!loading && !error">
          {{ totalCount }} person{{ totalCount !== 1 ? 's' : '' }}
        </span>
        <button class="btn-primary" @click="openCreateModal">
          + New Person
        </button>
      </div>
    </div>

    <div class="filters-bar">
      <div class="filter-group">
        <label>Project:</label>
        <select v-model="filterProjectId" @change="loadPersons">
          <option value="">All Projects</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>Organization:</label>
        <select v-model="filterOrganizationId" @change="loadPersons">
          <option value="">All Organizations</option>
          <option v-for="o in organizations" :key="o.id" :value="o.id">{{ o.name }}</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading persons...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadPersons" class="btn-primary">Retry</button>
    </div>

    <div v-else class="persons-content">
      <div v-if="persons.length === 0" class="empty-state">
        <p>No persons found</p>
        <p class="empty-state-hint">
          Add people you interact with during tasks and projects
        </p>
      </div>

      <div v-else class="persons-grid">
        <div 
          v-for="person in persons" 
          :key="person.id" 
          class="person-card"
        >
          <div class="person-header">
            <div class="person-avatar">
              {{ getInitials(person.name) }}
            </div>
            <div class="person-info">
              <h3 class="person-name">{{ person.name }}</h3>
              <span v-if="person.role" class="person-role">{{ person.role }}</span>
            </div>
            <div class="person-actions">
              <button class="btn-icon" @click="openEditModal(person)" title="Edit">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                  <path d="m15 5 4 4"/>
                </svg>
              </button>
              <button class="btn-icon danger" @click="handleDelete(person)" title="Delete">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 6h18"/>
                  <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                  <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="person-sections">
            <div 
              v-if="person.context" 
              class="section-chip"
              @click="openSectionViewer(person, 'context')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              Context
            </div>

            <div 
              v-if="person.next_step" 
              class="section-chip"
              @click="openSectionViewer(person, 'next_step')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"/>
                <path d="m12 5 7 7-7 7"/>
              </svg>
              Next Step
            </div>
          </div>

          <div class="person-links">
            <router-link 
              v-if="getProjectName(person.project_id)"
              :to="`/projects/${person.project_id}`"
              class="link-chip project"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
              </svg>
              {{ getProjectName(person.project_id) }}
            </router-link>

            <router-link 
              v-if="getOrganizationName(person.organization_id)"
              :to="`/organizations/${person.organization_id}`"
              class="link-chip organization"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              {{ getOrganizationName(person.organization_id) }}
            </router-link>
          </div>

          <div class="person-footer">
            <span v-if="person.last_met_date" class="meta-item">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>
                <line x1="16" x2="16" y1="2" y2="6"/>
                <line x1="8" x2="8" y1="2" y2="6"/>
                <line x1="3" x2="21" y1="10" y2="10"/>
              </svg>
              Last met: {{ formatDate(person.last_met_date) }}
            </span>
            <span v-else class="meta-item muted">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>
                <line x1="16" x2="16" y1="2" y2="6"/>
                <line x1="8" x2="8" y1="2" y2="6"/>
                <line x1="3" x2="21" y1="10" y2="10"/>
              </svg>
              No meeting recorded
            </span>
          </div>
        </div>
      </div>

      <div v-if="hasMore" class="load-more">
        <button @click="loadMore" class="btn-secondary">
          Load More ({{ persons.length }} of {{ totalCount }})
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
    <Modal 
      :show="showModal" 
      :title="isEditing ? 'Edit Person' : 'New Person'" 
      size="fullscreen" 
      @close="closeModal"
    >
      <form @submit.prevent="handleSubmit" class="person-form">
        <div class="form-row">
          <div class="form-group">
            <label for="name">Name *</label>
            <input 
              id="name" 
              v-model="formData.name" 
              type="text" 
              required 
              placeholder="Enter person's name"
            />
          </div>

          <div class="form-group">
            <label for="role">Role</label>
            <input 
              id="role" 
              v-model="formData.role" 
              type="text" 
              placeholder="e.g., Engineering Manager, Product Lead"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="project">Project</label>
            <select id="project" v-model="formData.project_id">
              <option :value="null">No project</option>
              <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>

          <div class="form-group">
            <label for="organization">Organization</label>
            <select id="organization" v-model="formData.organization_id">
              <option :value="null">No organization</option>
              <option v-for="o in organizations" :key="o.id" :value="o.id">{{ o.name }}</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label for="last_met_date">Last Met Date</label>
          <input 
            id="last_met_date" 
            v-model="formData.last_met_date" 
            type="datetime-local"
          />
        </div>

        <div class="form-group">
          <label>Context</label>
          <div class="markdown-editor-container">
            <div class="editor-tabs">
              <button 
                type="button" 
                :class="['tab-btn', { active: contextTab === 'write' }]"
                @click="contextTab = 'write'"
              >
                Write
              </button>
              <button 
                type="button" 
                :class="['tab-btn', { active: contextTab === 'preview' }]"
                @click="contextTab = 'preview'"
              >
                Preview
              </button>
            </div>
            <textarea 
              v-if="contextTab === 'write'"
              v-model="formData.context" 
              class="markdown-textarea"
              rows="5"
              placeholder="## Background

How you know this person, their responsibilities, key topics discussed.

### Notes
- Met during Q1 planning
- Technical lead for migration project"
            ></textarea>
            <div v-else class="markdown-preview" v-html="renderedContext"></div>
          </div>
          <span class="form-hint">Background and relationship context (supports Markdown)</span>
        </div>

        <div class="form-group">
          <label>Next Step</label>
          <div class="markdown-editor-container">
            <div class="editor-tabs">
              <button 
                type="button" 
                :class="['tab-btn', { active: nextStepTab === 'write' }]"
                @click="nextStepTab = 'write'"
              >
                Write
              </button>
              <button 
                type="button" 
                :class="['tab-btn', { active: nextStepTab === 'preview' }]"
                @click="nextStepTab = 'preview'"
              >
                Preview
              </button>
            </div>
            <textarea 
              v-if="nextStepTab === 'write'"
              v-model="formData.next_step" 
              class="markdown-textarea"
              rows="4"
              placeholder="- Schedule follow-up meeting
- Send proposal document
- Review technical requirements"
            ></textarea>
            <div v-else class="markdown-preview" v-html="renderedNextStep"></div>
          </div>
          <span class="form-hint">Planned follow-up actions (supports Markdown)</span>
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
import { marked } from 'marked'
import { personsApi, projectsApi, organizationsApi } from '@/services/api'
import Modal from '@/components/common/Modal.vue'

const persons = ref([])
const projects = ref([])
const organizations = ref([])
const totalCount = ref(0)
const currentSkip = ref(0)
const limit = 50
const loading = ref(false)
const error = ref(null)

// Filters
const filterProjectId = ref('')
const filterOrganizationId = ref('')

// Modal state
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const formData = ref({
  name: '',
  context: '',
  role: '',
  last_met_date: '',
  next_step: '',
  project_id: null,
  organization_id: null
})

// Editor tabs
const contextTab = ref('write')
const nextStepTab = ref('write')

// Section viewer modal state
const showSectionViewer = ref(false)
const viewingPerson = ref(null)
const viewingSection = ref('')

const hasMore = computed(() => {
  return persons.value.length < totalCount.value
})

const isFormValid = computed(() => {
  return formData.value.name && formData.value.name.trim().length > 0
})

// Rendered markdown for form fields
const renderedContext = computed(() => marked(formData.value.context || ''))
const renderedNextStep = computed(() => marked(formData.value.next_step || ''))

// Section viewer computeds
const sectionLabels = {
  context: 'Context',
  next_step: 'Next Step'
}

const sectionViewerTitle = computed(() => {
  if (!viewingPerson.value) return ''
  return `${viewingPerson.value.name} - ${sectionLabels[viewingSection.value] || ''}`
})

const renderedSectionContent = computed(() => {
  if (!viewingPerson.value || !viewingSection.value) return ''
  const content = viewingPerson.value[viewingSection.value] || ''
  return marked(content)
})

onMounted(async () => {
  await Promise.all([
    loadProjects(),
    loadOrganizations()
  ])
  await loadPersons()
})

async function loadProjects() {
  try {
    const response = await projectsApi.list({ limit: 500 })
    projects.value = response.data.projects
  } catch (err) {
    console.error('Failed to load projects:', err)
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

async function loadPersons() {
  loading.value = true
  error.value = null
  try {
    const params = { skip: 0, limit }
    if (filterProjectId.value) params.project_id = filterProjectId.value
    if (filterOrganizationId.value) params.organization_id = filterOrganizationId.value
    
    const response = await personsApi.list(params)
    persons.value = response.data.persons
    totalCount.value = response.data.total
    currentSkip.value = response.data.persons.length
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load persons'
    console.error('Failed to load persons:', err)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  try {
    const params = { skip: currentSkip.value, limit }
    if (filterProjectId.value) params.project_id = filterProjectId.value
    if (filterOrganizationId.value) params.organization_id = filterOrganizationId.value
    
    const response = await personsApi.list(params)
    persons.value = [...persons.value, ...response.data.persons]
    currentSkip.value = persons.value.length
  } catch (err) {
    console.error('Failed to load more persons:', err)
  }
}

function getInitials(name) {
  if (!name) return '?'
  const words = name.trim().split(/\s+/)
  if (words.length === 1) {
    return words[0].substring(0, 2).toUpperCase()
  }
  return (words[0][0] + words[1][0]).toUpperCase()
}

function getProjectName(projectId) {
  if (!projectId) return null
  const project = projects.value.find(p => p.id === projectId)
  return project?.name || null
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
    context: '',
    role: '',
    last_met_date: '',
    next_step: '',
    project_id: null,
    organization_id: null
  }
  resetTabs()
  showModal.value = true
}

function openEditModal(person) {
  isEditing.value = true
  editingId.value = person.id
  formData.value = {
    name: person.name,
    context: person.context || '',
    role: person.role || '',
    last_met_date: person.last_met_date ? formatDateTimeLocal(person.last_met_date) : '',
    next_step: person.next_step || '',
    project_id: person.project_id || null,
    organization_id: person.organization_id || null
  }
  resetTabs()
  showModal.value = true
}

function resetTabs() {
  contextTab.value = 'write'
  nextStepTab.value = 'write'
}

function closeModal() {
  showModal.value = false
  isEditing.value = false
  editingId.value = null
}

function openSectionViewer(person, section) {
  viewingPerson.value = person
  viewingSection.value = section
  showSectionViewer.value = true
}

function closeSectionViewer() {
  showSectionViewer.value = false
  viewingPerson.value = null
  viewingSection.value = ''
}

function editFromViewer() {
  const person = viewingPerson.value
  closeSectionViewer()
  if (person) {
    openEditModal(person)
  }
}

async function handleSubmit() {
  if (!isFormValid.value) return
  
  try {
    const payload = { ...formData.value }
    
    // Convert empty string to null for optional fields
    if (payload.project_id === null || payload.project_id === '') {
      delete payload.project_id
    }
    if (payload.organization_id === null || payload.organization_id === '') {
      delete payload.organization_id
    }
    if (!payload.last_met_date) {
      delete payload.last_met_date
    }
    
    if (isEditing.value) {
      const response = await personsApi.update(editingId.value, payload)
      const index = persons.value.findIndex(p => p.id === editingId.value)
      if (index !== -1) {
        persons.value[index] = response.data
      }
    } else {
      const response = await personsApi.create(payload)
      persons.value.unshift(response.data)
      totalCount.value++
    }
    closeModal()
  } catch (err) {
    console.error('Failed to save person:', err)
    alert(err.response?.data?.detail || 'Failed to save person')
  }
}

async function handleDelete(person) {
  if (confirm(`Delete "${person.name}"? This cannot be undone.`)) {
    try {
      await personsApi.delete(person.id)
      persons.value = persons.value.filter(p => p.id !== person.id)
      totalCount.value--
    } catch (err) {
      console.error('Failed to delete person:', err)
      alert(err.response?.data?.detail || 'Failed to delete person')
    }
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

function formatDateTimeLocal(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  // Format as YYYY-MM-DDTHH:mm for datetime-local input
  return date.toISOString().slice(0, 16)
}
</script>

<style scoped>
.persons-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .persons-view {
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

.person-count {
  padding: 0.375rem 0.75rem;
  background: #fef3c7;
  color: #92400e;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

:global(.dark) .person-count {
  background: #78350f;
  color: #fde68a;
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
  border-color: #d97706;
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.1);
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

.persons-content {
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

.persons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.person-card {
  background: white;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  padding: 1rem;
  transition: all 0.2s;
}

:global(.dark) .person-card {
  background: #1e293b;
  border-color: #334155;
}

.person-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.person-header {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.person-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.875rem;
  letter-spacing: -0.025em;
  flex-shrink: 0;
}

.person-info {
  flex: 1;
  min-width: 0;
}

.person-name {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:global(.dark) .person-name {
  color: #f1f5f9;
}

.person-role {
  font-size: 0.75rem;
  color: #6b7280;
}

:global(.dark) .person-role {
  color: #94a3b8;
}

.person-actions {
  display: flex;
  gap: 0.125rem;
  flex-shrink: 0;
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

.person-sections {
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
  background: #fef3c7;
  color: #92400e;
}

:global(.dark) .section-chip {
  background: #334155;
  color: #94a3b8;
}

:global(.dark) .section-chip:hover {
  background: #78350f;
  color: #fde68a;
}

.section-chip svg {
  opacity: 0.7;
}

.person-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-bottom: 0.75rem;
}

.link-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.6875rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.15s;
}

.link-chip.project {
  background: #dbeafe;
  color: #1e40af;
}

.link-chip.project:hover {
  background: #bfdbfe;
  color: #1d4ed8;
}

:global(.dark) .link-chip.project {
  background: rgba(37, 99, 235, 0.15);
  color: #60a5fa;
}

:global(.dark) .link-chip.project:hover {
  background: rgba(37, 99, 235, 0.25);
  color: #93c5fd;
}

.link-chip.organization {
  background: #e0e7ff;
  color: #3730a3;
}

.link-chip.organization:hover {
  background: #c7d2fe;
  color: #4338ca;
}

:global(.dark) .link-chip.organization {
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
}

:global(.dark) .link-chip.organization:hover {
  background: rgba(99, 102, 241, 0.25);
  color: #c7d2fe;
}

.person-footer {
  padding-top: 0.625rem;
  border-top: 1px solid #f3f4f6;
}

:global(.dark) .person-footer {
  border-top-color: #334155;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.6875rem;
  color: #6b7280;
}

.meta-item.muted {
  color: #9ca3af;
}

.meta-item svg {
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
  background-color: #d97706;
  color: white;
}

.btn-primary:hover {
  background-color: #b45309;
}

.btn-primary:disabled {
  background-color: #fcd34d;
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
.person-form {
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
  border-color: #d97706;
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.1);
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
  color: #d97706;
  border-bottom-color: #d97706;
  background: white;
}

:global(.dark) .tab-btn.active {
  background: #1e293b;
  color: #fbbf24;
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

.markdown-preview {
  padding: 0.75rem;
  min-height: 100px;
  max-height: 300px;
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
  min-height: 150px;
  max-height: 500px;
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
  color: #92400e;
}

:global(.dark) .markdown-preview :deep(h2) {
  color: #fbbf24;
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
  border-left: 3px solid #d97706;
  padding-left: 0.75rem;
  margin: 0.75rem 0;
  color: #4b5563;
  font-style: italic;
}

:global(.dark) .markdown-preview :deep(blockquote) {
  color: #94a3b8;
}

@media (max-width: 768px) {
  .persons-view {
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

  .persons-grid {
    grid-template-columns: 1fr;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>

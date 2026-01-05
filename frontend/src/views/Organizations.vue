<template>
  <div class="organizations-view">
    <div class="view-header">
      <div>
        <h2>Organizations</h2>
        <p class="view-description">
          Manage organization profiles, stakeholders, and strategy information
        </p>
      </div>
      <div class="header-actions">
        <span class="organization-count" v-if="!loading && !error">
          {{ totalCount }} organization{{ totalCount !== 1 ? 's' : '' }}
        </span>
        <button class="btn-primary" @click="openCreateModal">
          + New Organization
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading organizations...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadOrganizations" class="btn-primary">Retry</button>
    </div>

    <div v-else class="organizations-content">
      <div v-if="organizations.length === 0" class="empty-state">
        <p>No organizations found</p>
        <p class="empty-state-hint">
          Add organizations to track stakeholders and strategy information
        </p>
      </div>

      <div v-else class="organizations-grid">
        <div 
          v-for="organization in organizations" 
          :key="organization.id" 
          class="organization-card"
        >
          <div class="organization-header">
            <div class="organization-avatar">
              {{ getInitials(organization.name) }}
            </div>
            <div class="organization-info">
              <h3 class="organization-name">{{ organization.name }}</h3>
              <span class="meta-date">{{ formatDate(organization.created_at) }}</span>
            </div>
            <div class="organization-actions">
              <button class="btn-icon" @click="openEditModal(organization)" title="Edit">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                  <path d="m15 5 4 4"/>
                </svg>
              </button>
              <button class="btn-icon danger" @click="handleDelete(organization)" title="Delete">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 6h18"/>
                  <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                  <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="organization-sections">
            <div 
              v-if="organization.stakeholders" 
              class="section-chip"
              @click="openSectionViewer(organization, 'stakeholders')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              Stakeholders
            </div>

            <div 
              v-if="organization.team" 
              class="section-chip"
              @click="openSectionViewer(organization, 'team')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              Team
            </div>

            <div 
              v-if="organization.description" 
              class="section-chip"
              @click="openSectionViewer(organization, 'description')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              Strategy
            </div>

            <div 
              v-if="organization.related_products" 
              class="section-chip"
              @click="openSectionViewer(organization, 'related_products')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m7.5 4.27 9 5.15"/>
                <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>
                <path d="m3.3 7 8.7 5 8.7-5"/>
                <path d="M12 22V12"/>
              </svg>
              Products
            </div>
          </div>

          <div class="organization-footer">
            <router-link 
              :to="{ path: '/projects', query: { organization: organization.id } }" 
              class="view-projects-link"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
              </svg>
              View Projects
            </router-link>
          </div>
        </div>
      </div>

      <div v-if="hasMore" class="load-more">
        <button @click="loadMore" class="btn-secondary">
          Load More ({{ organizations.length }} of {{ totalCount }})
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
      :title="isEditing ? 'Edit Organization' : 'New Organization'" 
      size="fullscreen" 
      @close="closeModal"
    >
      <form @submit.prevent="handleSubmit" class="organization-form">
        <div class="form-group">
          <label for="name">Organization Name *</label>
          <input 
            id="name" 
            v-model="formData.name" 
            type="text" 
            required 
            placeholder="Enter organization or company name"
          />
        </div>

        <div class="form-group">
          <label>Stakeholders</label>
          <div class="markdown-editor-container">
            <div class="editor-tabs">
              <button 
                type="button" 
                :class="['tab-btn', { active: stakeholdersTab === 'write' }]"
                @click="stakeholdersTab = 'write'"
              >
                Write
              </button>
              <button 
                type="button" 
                :class="['tab-btn', { active: stakeholdersTab === 'preview' }]"
                @click="stakeholdersTab = 'preview'"
              >
                Preview
              </button>
            </div>
            <textarea 
              v-if="stakeholdersTab === 'write'"
              v-model="formData.stakeholders" 
              class="markdown-textarea"
              rows="4"
              placeholder="## Key Contacts
- **John Doe** - CTO, decision maker
- **Jane Smith** - PM, technical lead"
            ></textarea>
            <div v-else class="markdown-preview" v-html="renderedStakeholders"></div>
          </div>
          <span class="form-hint">Key decision makers and contacts (supports Markdown)</span>
        </div>

        <div class="form-group">
          <label>Team</label>
          <div class="markdown-editor-container">
            <div class="editor-tabs">
              <button 
                type="button" 
                :class="['tab-btn', { active: teamTab === 'write' }]"
                @click="teamTab = 'write'"
              >
                Write
              </button>
              <button 
                type="button" 
                :class="['tab-btn', { active: teamTab === 'preview' }]"
                @click="teamTab = 'preview'"
              >
                Preview
              </button>
            </div>
            <textarea 
              v-if="teamTab === 'write'"
              v-model="formData.team" 
              class="markdown-textarea"
              rows="4"
              placeholder="## Internal Team
- **Account Manager**: Alex Johnson
- **Technical Lead**: Sarah Chen"
            ></textarea>
            <div v-else class="markdown-preview" v-html="renderedTeam"></div>
          </div>
          <span class="form-hint">Your team members assigned to this organization (supports Markdown)</span>
        </div>

        <div class="form-group">
          <label>Strategy / Notes</label>
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
              placeholder="## Account Strategy

### Goals
- Expand platform adoption
- Upsell enterprise features

### Notes
- Q1 budget approved
- Decision timeline: March 2026"
            ></textarea>
            <div v-else class="markdown-preview" v-html="renderedDescription"></div>
          </div>
          <span class="form-hint">Overall strategy and relationship notes (supports Markdown)</span>
        </div>

        <div class="form-group">
          <label>Related Products</label>
          <div class="markdown-editor-container">
            <div class="editor-tabs">
              <button 
                type="button" 
                :class="['tab-btn', { active: productsTab === 'write' }]"
                @click="productsTab = 'write'"
              >
                Write
              </button>
              <button 
                type="button" 
                :class="['tab-btn', { active: productsTab === 'preview' }]"
                @click="productsTab = 'preview'"
              >
                Preview
              </button>
            </div>
            <textarea 
              v-if="productsTab === 'write'"
              v-model="formData.related_products" 
              class="markdown-textarea"
              rows="4"
              placeholder="## Products in Use
- **Flink SQL** - Production
- **Kafka Streams** - Evaluation"
            ></textarea>
            <div v-else class="markdown-preview" v-html="renderedProducts"></div>
          </div>
          <span class="form-hint">Products, services, or solutions relevant to this organization (supports Markdown)</span>
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
import { organizationsApi } from '@/services/api'
import Modal from '@/components/common/Modal.vue'

const organizations = ref([])
const totalCount = ref(0)
const currentSkip = ref(0)
const limit = 50
const loading = ref(false)
const error = ref(null)

// Modal state
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const formData = ref({
  name: '',
  stakeholders: '',
  team: '',
  description: '',
  related_products: ''
})

// Editor tabs for each section
const stakeholdersTab = ref('write')
const teamTab = ref('write')
const descriptionTab = ref('write')
const productsTab = ref('write')

// Section viewer modal state
const showSectionViewer = ref(false)
const viewingOrganization = ref(null)
const viewingSection = ref('')

const hasMore = computed(() => {
  return organizations.value.length < totalCount.value
})

const isFormValid = computed(() => {
  return formData.value.name && formData.value.name.trim().length > 0
})

// Rendered markdown for form fields
const renderedStakeholders = computed(() => marked(formData.value.stakeholders || ''))
const renderedTeam = computed(() => marked(formData.value.team || ''))
const renderedDescription = computed(() => marked(formData.value.description || ''))
const renderedProducts = computed(() => marked(formData.value.related_products || ''))

// Section viewer computeds
const sectionLabels = {
  stakeholders: 'Stakeholders',
  team: 'Team',
  description: 'Strategy / Notes',
  related_products: 'Related Products'
}

const sectionViewerTitle = computed(() => {
  if (!viewingOrganization.value) return ''
  return `${viewingOrganization.value.name} - ${sectionLabels[viewingSection.value] || ''}`
})

const renderedSectionContent = computed(() => {
  if (!viewingOrganization.value || !viewingSection.value) return ''
  const content = viewingOrganization.value[viewingSection.value] || ''
  return marked(content)
})

onMounted(async () => {
  await loadOrganizations()
})

async function loadOrganizations() {
  loading.value = true
  error.value = null
  try {
    const response = await organizationsApi.list({ skip: 0, limit })
    organizations.value = response.data.organizations
    totalCount.value = response.data.total
    currentSkip.value = response.data.organizations.length
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load organizations'
    console.error('Failed to load organizations:', err)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  try {
    const response = await organizationsApi.list({ skip: currentSkip.value, limit })
    organizations.value = [...organizations.value, ...response.data.organizations]
    currentSkip.value = organizations.value.length
  } catch (err) {
    console.error('Failed to load more organizations:', err)
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

function openCreateModal() {
  isEditing.value = false
  editingId.value = null
  formData.value = {
    name: '',
    stakeholders: '',
    team: '',
    description: '',
    related_products: ''
  }
  resetTabs()
  showModal.value = true
}

function openEditModal(organization) {
  isEditing.value = true
  editingId.value = organization.id
  formData.value = {
    name: organization.name,
    stakeholders: organization.stakeholders || '',
    team: organization.team || '',
    description: organization.description || '',
    related_products: organization.related_products || ''
  }
  resetTabs()
  showModal.value = true
}

function resetTabs() {
  stakeholdersTab.value = 'write'
  teamTab.value = 'write'
  descriptionTab.value = 'write'
  productsTab.value = 'write'
}

function closeModal() {
  showModal.value = false
  isEditing.value = false
  editingId.value = null
}

function openSectionViewer(organization, section) {
  viewingOrganization.value = organization
  viewingSection.value = section
  showSectionViewer.value = true
}

function closeSectionViewer() {
  showSectionViewer.value = false
  viewingOrganization.value = null
  viewingSection.value = ''
}

function editFromViewer() {
  const org = viewingOrganization.value
  closeSectionViewer()
  if (org) {
    openEditModal(org)
  }
}

async function handleSubmit() {
  if (!isFormValid.value) return
  
  try {
    if (isEditing.value) {
      const response = await organizationsApi.update(editingId.value, formData.value)
      const index = organizations.value.findIndex(o => o.id === editingId.value)
      if (index !== -1) {
        organizations.value[index] = response.data
      }
    } else {
      const response = await organizationsApi.create(formData.value)
      organizations.value.unshift(response.data)
      totalCount.value++
    }
    closeModal()
  } catch (err) {
    console.error('Failed to save organization:', err)
    alert(err.response?.data?.detail || 'Failed to save organization')
  }
}

async function handleDelete(organization) {
  if (confirm(`Delete organization "${organization.name}"? This will not delete associated projects.`)) {
    try {
      await organizationsApi.delete(organization.id)
      organizations.value = organizations.value.filter(o => o.id !== organization.id)
      totalCount.value--
    } catch (err) {
      console.error('Failed to delete organization:', err)
      alert(err.response?.data?.detail || 'Failed to delete organization')
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
</script>

<style scoped>
.organizations-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .organizations-view {
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

.organization-count {
  padding: 0.375rem 0.75rem;
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

:global(.dark) .organization-count {
  background: #312e81;
  color: #a5b4fc;
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

.organizations-content {
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

.organizations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.organization-card {
  background: white;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  padding: 1rem;
  transition: all 0.2s;
}

:global(.dark) .organization-card {
  background: #1e293b;
  border-color: #334155;
}

.organization-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.organization-header {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.organization-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.8125rem;
  letter-spacing: -0.025em;
  flex-shrink: 0;
}

.organization-info {
  flex: 1;
  min-width: 0;
}

.organization-name {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 600;
  color: #111827;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:global(.dark) .organization-name {
  color: #f1f5f9;
}

.meta-date {
  font-size: 0.6875rem;
  color: #9ca3af;
}

.organization-actions {
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

.organization-sections {
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
  background: #e0e7ff;
  color: #3730a3;
}

:global(.dark) .section-chip {
  background: #334155;
  color: #94a3b8;
}

:global(.dark) .section-chip:hover {
  background: #312e81;
  color: #a5b4fc;
}

.section-chip svg {
  opacity: 0.7;
}

.organization-footer {
  padding-top: 0.625rem;
  border-top: 1px solid #f3f4f6;
}

:global(.dark) .organization-footer {
  border-top-color: #334155;
}

.view-projects-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.6875rem;
  font-weight: 500;
  color: #7c3aed;
  text-decoration: none;
  background: #f5f3ff;
  border-radius: 4px;
  transition: all 0.15s;
}

.view-projects-link:hover {
  background: #ede9fe;
  color: #6d28d9;
}

:global(.dark) .view-projects-link {
  background: rgba(124, 58, 237, 0.15);
  color: #a78bfa;
}

:global(.dark) .view-projects-link:hover {
  background: rgba(124, 58, 237, 0.25);
  color: #c4b5fd;
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
.organization-form {
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

.form-group input {
  padding: 0.625rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9375rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}

:global(.dark) .form-group input {
  background: #1e293b;
  border-color: #334155;
  color: #f1f5f9;
}

.form-group input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
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

@media (max-width: 768px) {
  .organizations-view {
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

  .organizations-grid {
    grid-template-columns: 1fr;
  }
}
</style>

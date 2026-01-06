<template>
  <div class="organization-detail-view">
    <div class="view-header">
      <div class="header-left">
        <router-link to="/organizations" class="back-link">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
          Back to Organizations
        </router-link>
        <h2 v-if="organization">{{ organization.name }}</h2>
        <h2 v-else-if="loading">Loading...</h2>
      </div>
      <div class="header-actions" v-if="organization">
        <button class="btn-secondary" @click="editOrganization">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
            <path d="m15 5 4 4"/>
          </svg>
          Edit
        </button>
        <router-link 
          :to="{ path: '/projects', query: { organization: organization.id } }" 
          class="btn-primary"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
          View Projects
        </router-link>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading organization...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadOrganization" class="btn-primary">Retry</button>
    </div>

    <div v-else-if="organization" class="organization-content">
      <div class="organization-meta">
        <div class="meta-item">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>
            <line x1="16" x2="16" y1="2" y2="6"/>
            <line x1="8" x2="8" y1="2" y2="6"/>
            <line x1="3" x2="21" y1="10" y2="10"/>
          </svg>
          Created {{ formatDate(organization.created_at) }}
        </div>
        <div class="meta-item" v-if="organization.updated_at !== organization.created_at">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/>
            <path d="M21 3v5h-5"/>
          </svg>
          Updated {{ formatDate(organization.updated_at) }}
        </div>
      </div>

      <div class="sections-grid">
        <div class="section-card" v-if="organization.stakeholders">
          <div class="section-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            <h3>Stakeholders</h3>
          </div>
          <div class="section-content markdown-preview" v-html="renderedStakeholders"></div>
        </div>

        <div class="section-card" v-if="organization.team">
          <div class="section-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            <h3>Team</h3>
          </div>
          <div class="section-content markdown-preview" v-html="renderedTeam"></div>
        </div>

        <div class="section-card full-width" v-if="organization.description">
          <div class="section-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <h3>Strategy / Notes</h3>
          </div>
          <div class="section-content markdown-preview" v-html="renderedDescription"></div>
        </div>

        <div class="section-card" v-if="organization.related_products">
          <div class="section-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m7.5 4.27 9 5.15"/>
              <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>
              <path d="m3.3 7 8.7 5 8.7-5"/>
              <path d="M12 22V12"/>
            </svg>
            <h3>Related Products</h3>
          </div>
          <div class="section-content markdown-preview" v-html="renderedProducts"></div>
        </div>
      </div>

      <div class="empty-content" v-if="!hasContent">
        <p>No content has been added to this organization yet.</p>
        <button class="btn-primary" @click="editOrganization">Add Content</button>
      </div>
    </div>

    <!-- Edit Modal -->
    <Modal 
      :show="showEditModal" 
      title="Edit Organization" 
      size="fullscreen" 
      @close="closeEditModal"
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
            <div v-else class="markdown-preview form-preview" v-html="formRenderedStakeholders"></div>
          </div>
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
            <div v-else class="markdown-preview form-preview" v-html="formRenderedTeam"></div>
          </div>
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
- Upsell enterprise features"
            ></textarea>
            <div v-else class="markdown-preview form-preview" v-html="formRenderedDescription"></div>
          </div>
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
            <div v-else class="markdown-preview form-preview" v-html="formRenderedProducts"></div>
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
import { organizationsApi } from '@/services/api'
import Modal from '@/components/common/Modal.vue'

const route = useRoute()
const router = useRouter()

const organization = ref(null)
const loading = ref(false)
const error = ref(null)

// Edit modal state
const showEditModal = ref(false)
const formData = ref({
  name: '',
  stakeholders: '',
  team: '',
  description: '',
  related_products: ''
})

// Editor tabs
const stakeholdersTab = ref('write')
const teamTab = ref('write')
const descriptionTab = ref('write')
const productsTab = ref('write')

// Computed for rendered markdown (view mode)
const renderedStakeholders = computed(() => marked(organization.value?.stakeholders || ''))
const renderedTeam = computed(() => marked(organization.value?.team || ''))
const renderedDescription = computed(() => marked(organization.value?.description || ''))
const renderedProducts = computed(() => marked(organization.value?.related_products || ''))

// Computed for form rendered markdown
const formRenderedStakeholders = computed(() => marked(formData.value.stakeholders || ''))
const formRenderedTeam = computed(() => marked(formData.value.team || ''))
const formRenderedDescription = computed(() => marked(formData.value.description || ''))
const formRenderedProducts = computed(() => marked(formData.value.related_products || ''))

const hasContent = computed(() => {
  if (!organization.value) return false
  return organization.value.stakeholders || 
         organization.value.team || 
         organization.value.description || 
         organization.value.related_products
})

const isFormValid = computed(() => {
  return formData.value.name && formData.value.name.trim().length > 0
})

onMounted(async () => {
  await loadOrganization()
})

async function loadOrganization() {
  const id = route.params.id
  if (!id) {
    error.value = 'Organization ID not provided'
    return
  }

  loading.value = true
  error.value = null
  try {
    const response = await organizationsApi.get(id)
    organization.value = response.data
  } catch (err) {
    if (err.response?.status === 404) {
      error.value = 'Organization not found'
    } else {
      error.value = err.response?.data?.detail || 'Failed to load organization'
    }
    console.error('Failed to load organization:', err)
  } finally {
    loading.value = false
  }
}

function editOrganization() {
  formData.value = {
    name: organization.value.name,
    stakeholders: organization.value.stakeholders || '',
    team: organization.value.team || '',
    description: organization.value.description || '',
    related_products: organization.value.related_products || ''
  }
  resetTabs()
  showEditModal.value = true
}

function resetTabs() {
  stakeholdersTab.value = 'write'
  teamTab.value = 'write'
  descriptionTab.value = 'write'
  productsTab.value = 'write'
}

function closeEditModal() {
  showEditModal.value = false
}

async function handleSubmit() {
  if (!isFormValid.value) return
  
  try {
    const response = await organizationsApi.update(organization.value.id, formData.value)
    organization.value = response.data
    closeEditModal()
  } catch (err) {
    console.error('Failed to update organization:', err)
    alert(err.response?.data?.detail || 'Failed to update organization')
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
.organization-detail-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .organization-detail-view {
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

.organization-meta {
  display: flex;
  gap: 1.5rem;
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

.organization-content {
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
  .organization-detail-view {
    padding: 1rem;
  }

  .view-header {
    flex-direction: column;
    gap: 1rem;
  }

  .header-actions {
    width: 100%;
  }

  .organization-meta {
    flex-direction: column;
    gap: 0.5rem;
  }

  .sections-grid {
    grid-template-columns: 1fr;
  }

  .section-card.full-width {
    grid-column: 1;
  }
}
</style>



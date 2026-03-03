<template>
  <div class="organization-edit-view">
    <div class="view-header">
      <div class="header-left">
        <router-link :to="backLink" class="back-link">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
          Back to organization
        </router-link>
        <h2 v-if="organization">{{ organization.name }}</h2>
        <h2 v-else-if="loading">Loading...</h2>
        <h2 v-else>Edit Organization</h2>
      </div>
      <div class="header-actions" v-if="organization">
        <div class="preview-toggle-wrap">
          <button
            type="button"
            :class="['toggle-btn', { active: !fullPagePreview }]"
            @click="fullPagePreview = false"
            title="Edit mode"
          >
            Edit
          </button>
          <button
            type="button"
            :class="['toggle-btn', { active: fullPagePreview }]"
            @click="fullPagePreview = true"
            title="Preview full page"
          >
            Preview
          </button>
        </div>
        <span class="save-status" v-if="saving">Saving...</span>
        <span class="save-status saved" v-else-if="lastSavedAt">
          Saved {{ formatTime(lastSavedAt) }}
        </span>
        <span class="save-status error" v-else-if="lastSaveError" :title="lastSaveError">
          Save failed
        </span>
        <button
          v-if="!fullPagePreview"
          type="button"
          class="btn-primary"
          @click="saveNow"
          :disabled="!isFormValid || saving"
        >
          Save
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading organization...</p>
    </div>

    <div v-else-if="loadError" class="error-state">
      <p>{{ loadError }}</p>
      <button @click="loadOrganization" class="btn-primary">Retry</button>
    </div>

    <div v-else-if="organization && fullPagePreview" class="full-page-preview">
      <div class="preview-section">
        <h3 class="preview-section-title">Organization Name</h3>
        <p class="preview-name">{{ formData.name || '—' }}</p>
      </div>
      <div class="preview-section" v-if="formData.stakeholders">
        <h3 class="preview-section-title">Stakeholders</h3>
        <div class="markdown-preview form-preview" v-html="formRenderedStakeholders"></div>
      </div>
      <div class="preview-section" v-if="formData.team">
        <h3 class="preview-section-title">Team</h3>
        <div class="markdown-preview form-preview" v-html="formRenderedTeam"></div>
      </div>
      <div class="preview-section" v-if="formData.description">
        <h3 class="preview-section-title">Strategy / Notes</h3>
        <div class="markdown-preview form-preview" v-html="formRenderedDescription"></div>
      </div>
      <div class="preview-section" v-if="formData.related_products">
        <h3 class="preview-section-title">Related Products</h3>
        <div class="markdown-preview form-preview" v-html="formRenderedProducts"></div>
      </div>
    </div>

    <form v-else-if="organization" @submit.prevent="saveNow" class="organization-form">
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
            <button type="button" :class="['tab-btn', { active: stakeholdersTab === 'write' }]" @click="stakeholdersTab = 'write'">Write</button>
            <button type="button" :class="['tab-btn', { active: stakeholdersTab === 'preview' }]" @click="stakeholdersTab = 'preview'">Preview</button>
          </div>
          <textarea
            v-if="stakeholdersTab === 'write'"
            v-model="formData.stakeholders"
            class="markdown-textarea"
            rows="3"
            placeholder="## Key Contacts
- **John Doe** - CTO, decision maker
- **Jane Smith** - PM, technical lead"
          />
          <div v-else class="markdown-preview form-preview" v-html="formRenderedStakeholders"></div>
        </div>
      </div>

      <div class="form-group">
        <label>Team</label>
        <div class="markdown-editor-container">
          <div class="editor-tabs">
            <button type="button" :class="['tab-btn', { active: teamTab === 'write' }]" @click="teamTab = 'write'">Write</button>
            <button type="button" :class="['tab-btn', { active: teamTab === 'preview' }]" @click="teamTab = 'preview'">Preview</button>
          </div>
          <textarea
            v-if="teamTab === 'write'"
            v-model="formData.team"
            class="markdown-textarea"
            rows="3"
            placeholder="## Internal Team
- **Account Manager**: Alex Johnson
- **Technical Lead**: Sarah Chen"
          />
          <div v-else class="markdown-preview form-preview" v-html="formRenderedTeam"></div>
        </div>
      </div>

      <div class="form-group">
        <label>Strategy / Notes</label>
        <div class="markdown-editor-container">
          <div class="editor-tabs">
            <button type="button" :class="['tab-btn', { active: descriptionTab === 'write' }]" @click="descriptionTab = 'write'">Write</button>
            <button type="button" :class="['tab-btn', { active: descriptionTab === 'preview' }]" @click="descriptionTab = 'preview'">Preview</button>
          </div>
          <textarea
            v-if="descriptionTab === 'write'"
            v-model="formData.description"
            class="markdown-textarea"
            rows="15"
            placeholder="## Account Strategy

### Goals
- Expand platform adoption
- Upsell enterprise features"
          />
          <div v-else class="markdown-preview form-preview" v-html="formRenderedDescription"></div>
        </div>
      </div>

      <div class="form-group">
        <label>Related Products</label>
        <div class="markdown-editor-container">
          <div class="editor-tabs">
            <button type="button" :class="['tab-btn', { active: productsTab === 'write' }]" @click="productsTab = 'write'">Write</button>
            <button type="button" :class="['tab-btn', { active: productsTab === 'preview' }]" @click="productsTab = 'preview'">Preview</button>
          </div>
          <textarea
            v-if="productsTab === 'write'"
            v-model="formData.related_products"
            class="markdown-textarea"
            rows="2"
            placeholder="## Products in Use
- **Flink SQL** - Production
- **Kafka Streams** - Evaluation"
          />
          <div v-else class="markdown-preview form-preview" v-html="formRenderedProducts"></div>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { organizationsApi } from '@/services/api'

const route = useRoute()

const organization = ref(null)
const loading = ref(false)
const loadError = ref(null)

const formData = ref({
  name: '',
  stakeholders: '',
  team: '',
  description: '',
  related_products: ''
})

const stakeholdersTab = ref('write')
const teamTab = ref('write')
const descriptionTab = ref('write')
const productsTab = ref('write')

const fullPagePreview = ref(false)
const saving = ref(false)
const lastSaveError = ref(null)
const lastSavedAt = ref(null)
const initialLoadDone = ref(false)

const DEBOUNCE_MS = 2500
let debounceTimer = null

const orgId = computed(() => route.params.id)
const backLink = computed(() => (orgId.value ? { name: 'OrganizationDetail', params: { id: orgId.value } } : '/organizations'))

const isFormValid = computed(() => formData.value.name && formData.value.name.trim().length > 0)

const formRenderedStakeholders = computed(() => marked(formData.value.stakeholders || ''))
const formRenderedTeam = computed(() => marked(formData.value.team || ''))
const formRenderedDescription = computed(() => marked(formData.value.description || ''))
const formRenderedProducts = computed(() => marked(formData.value.related_products || ''))

const defaultStakeholders = `## Key Contacts
- **Name** - Role, responsibilities
- **Name** - Role, responsibilities`
const defaultTeam = `## Internal Team
- **Account Manager**: Name
- **Technical Lead**: Name`
const defaultDescription = `## Account Strategy

### Goals
- Goal 1
- Goal 2

### Current Status
Brief overview of current engagement

### Next Steps
- Action item 1
- Action item 2`
const defaultProducts = `## Products in Use
- **Product Name** - Status (Production/Evaluation/POC)
- **Product Name** - Status`

function fillFormFromOrg(org) {
  formData.value = {
    name: org.name,
    stakeholders: org.stakeholders || defaultStakeholders,
    team: org.team || defaultTeam,
    description: org.description || defaultDescription,
    related_products: org.related_products || defaultProducts
  }
}

onMounted(async () => {
  await loadOrganization()
})

watch(orgId, async (newId, oldId) => {
  if (newId && newId !== oldId) {
    initialLoadDone.value = false
    organization.value = null
    loadError.value = null
    await loadOrganization()
  }
})

async function loadOrganization() {
  const id = orgId.value
  if (!id) {
    loadError.value = 'Organization ID not provided'
    return
  }
  loading.value = true
  loadError.value = null
  try {
    const response = await organizationsApi.get(id)
    organization.value = response.data
    fillFormFromOrg(response.data)
    initialLoadDone.value = true
  } catch (err) {
    if (err.response?.status === 404) {
      loadError.value = 'Organization not found'
    } else {
      loadError.value = err.response?.data?.detail || 'Failed to load organization'
    }
    console.error('Failed to load organization:', err)
  } finally {
    loading.value = false
  }
}

async function performSave() {
  if (!organization.value || !isFormValid.value) return
  saving.value = true
  lastSaveError.value = null
  try {
    const response = await organizationsApi.update(organization.value.id, {
      name: formData.value.name.trim(),
      stakeholders: formData.value.stakeholders || '',
      team: formData.value.team || '',
      description: formData.value.description || '',
      related_products: formData.value.related_products || ''
    })
    organization.value = response.data
    lastSavedAt.value = new Date()
  } catch (err) {
    lastSaveError.value = err.response?.data?.detail || 'Failed to save'
    console.error('Failed to save organization:', err)
  } finally {
    saving.value = false
  }
}

function debouncedSave() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    debounceTimer = null
    performSave()
  }, DEBOUNCE_MS)
}

function saveNow() {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
  performSave()
}

watch(
  formData,
  () => {
    if (!initialLoadDone.value || !organization.value) return
    debouncedSave()
  },
  { deep: true }
)

function formatTime(date) {
  if (!date) return ''
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
</script>

<style scoped>
.organization-edit-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .organization-edit-view {
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

.save-status {
  font-size: 0.875rem;
  color: #6b7280;
}

.save-status.saved {
  color: #059669;
}

:global(.dark) .save-status.saved {
  color: #34d399;
}

.save-status.error {
  color: #dc2626;
}

:global(.dark) .save-status.error {
  color: #f87171;
}

.preview-toggle-wrap {
  display: flex;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  overflow: hidden;
  background: white;
}

:global(.dark) .preview-toggle-wrap {
  border-color: #334155;
  background: #1e293b;
}

.preview-toggle-wrap .toggle-btn {
  padding: 0.5rem 0.75rem;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.preview-toggle-wrap .toggle-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

:global(.dark) .preview-toggle-wrap .toggle-btn:hover {
  background: #334155;
  color: #f1f5f9;
}

.preview-toggle-wrap .toggle-btn.active {
  background: #e0e7ff;
  color: #3730a3;
}

:global(.dark) .preview-toggle-wrap .toggle-btn.active {
  background: #312e81;
  color: #a5b4fc;
}

.full-page-preview {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 48rem;
}

.preview-section {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem 1.25rem;
}

:global(.dark) .preview-section {
  background: #1e293b;
  border-color: #334155;
}

.preview-section-title {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

:global(.dark) .preview-section-title {
  color: #94a3b8;
}

.preview-name {
  margin: 0;
  font-size: 1.125rem;
  color: #111827;
}

:global(.dark) .preview-name {
  color: #f1f5f9;
}

.full-page-preview .markdown-preview.form-preview {
  padding: 0;
  min-height: 0;
  max-height: none;
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

.markdown-preview.form-preview {
  padding: 0.75rem;
  min-height: 100px;
  max-height: 300px;
  overflow-y: auto;
  background: white;
  line-height: 1.6;
  font-size: 0.875rem;
}

:global(.dark) .markdown-preview.form-preview {
  background: #1e293b;
  color: #e2e8f0;
}

.markdown-preview.form-preview :deep(h1) { font-size: 1.25rem; margin: 0 0 0.5rem 0; }
.markdown-preview.form-preview :deep(h2) { font-size: 1.125rem; margin: 0.75rem 0 0.375rem 0; }
.markdown-preview.form-preview :deep(h3) { font-size: 1rem; margin: 0.5rem 0 0.25rem 0; }
.markdown-preview.form-preview :deep(ul), .markdown-preview.form-preview :deep(ol) { padding-left: 1.25rem; margin: 0 0 0.5rem 0; }

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  border: none;
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

@media (max-width: 768px) {
  .organization-edit-view {
    padding: 1rem;
  }

  .view-header {
    flex-direction: column;
    gap: 1rem;
  }

  .header-actions {
    flex-wrap: wrap;
  }
}
</style>

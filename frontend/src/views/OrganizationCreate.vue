<template>
  <div class="organization-create-view">
    <div class="view-header">
      <div class="header-left">
        <router-link to="/organizations" class="back-link">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
          Back to organizations
        </router-link>
        <h2>New Organization</h2>
      </div>
      <div class="header-actions">
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
        <button
          v-if="!fullPagePreview"
          type="button"
          class="btn-primary"
          @click="handleCreate"
          :disabled="!isFormValid || submitting"
        >
          Create
        </button>
      </div>
    </div>

    <div v-if="fullPagePreview" class="full-page-preview">
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

    <form v-else @submit.prevent="handleCreate" class="organization-form">
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
        <span class="form-hint">Key decision makers and contacts (supports Markdown)</span>
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
        <span class="form-hint">Your team members assigned to this organization (supports Markdown)</span>
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
            rows="6"
            placeholder="## Account Strategy

### Goals
- Expand platform adoption
- Upsell enterprise features"
          />
          <div v-else class="markdown-preview form-preview" v-html="formRenderedDescription"></div>
        </div>
        <span class="form-hint">Overall strategy and relationship notes (supports Markdown)</span>
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
        <span class="form-hint">Products, services, or solutions relevant to this organization (supports Markdown)</span>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import { organizationsApi } from '@/services/api'

const router = useRouter()

const formData = ref({
  name: '',
  stakeholders: `## Key Contacts
- **Name** - Role, responsibilities
- **Name** - Role, responsibilities`,
  team: `## Internal Team
- **Account Manager**: Name
- **Technical Lead**: Name`,
  description: `## Account Strategy

### Goals
- Goal 1
- Goal 2

### Current Status
Brief overview of current engagement

### Next Steps
- Action item 1
- Action item 2`,
  related_products: `## Products in Use
- **Product Name** - Status (Production/Evaluation/POC)
- **Product Name** - Status`
})

const stakeholdersTab = ref('write')
const teamTab = ref('write')
const descriptionTab = ref('write')
const productsTab = ref('write')
const fullPagePreview = ref(false)
const submitting = ref(false)

const isFormValid = computed(() => formData.value.name && formData.value.name.trim().length > 0)

const formRenderedStakeholders = computed(() => marked(formData.value.stakeholders || ''))
const formRenderedTeam = computed(() => marked(formData.value.team || ''))
const formRenderedDescription = computed(() => marked(formData.value.description || ''))
const formRenderedProducts = computed(() => marked(formData.value.related_products || ''))

async function handleCreate() {
  if (!isFormValid.value) return
  submitting.value = true
  try {
    const response = await organizationsApi.create(formData.value)
    router.push({ name: 'OrganizationDetail', params: { id: response.data.id } })
  } catch (err) {
    console.error('Failed to create organization:', err)
    alert(err.response?.data?.detail || 'Failed to create organization')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.organization-create-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .organization-create-view {
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

.organization-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 48rem;
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
}

:global(.dark) .form-group input {
  background: #1e293b;
  border-color: #334155;
  color: #f1f5f9;
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
  border-bottom: 2px solid transparent;
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

.form-hint {
  font-size: 0.75rem;
  color: #6b7280;
}

.btn-primary {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  background-color: #2563eb;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #1d4ed8;
}

.btn-primary:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .organization-create-view {
    padding: 1rem;
  }
}
</style>

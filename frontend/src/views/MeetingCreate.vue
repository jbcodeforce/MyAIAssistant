<template>
  <div class="meeting-create-view">
    <div class="view-header">
      <div class="header-left">
        <router-link to="/meetings" class="back-link">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
          Back to meeting notes
        </router-link>
        <h2>New Meeting Note</h2>
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
          Create Meeting Note
        </button>
      </div>
    </div>

    <div v-if="fullPagePreview" class="full-page-preview">
      <div class="preview-section">
        <h3 class="preview-section-title">Meeting ID</h3>
        <p class="preview-name">{{ formData.meeting_id || '—' }}</p>
      </div>
      <div class="preview-section" v-if="formData.org_id">
        <h3 class="preview-section-title">Organization</h3>
        <p class="preview-name">{{ getOrganizationName(formData.org_id) }}</p>
      </div>
      <div class="preview-section" v-if="formData.project_id">
        <h3 class="preview-section-title">Project</h3>
        <p class="preview-name">{{ getProjectName(formData.project_id) }}</p>
      </div>
      <div class="preview-section" v-if="formData.presents">
        <h3 class="preview-section-title">Attendees</h3>
        <p class="preview-name">{{ formData.presents }}</p>
      </div>
      <div class="preview-section" v-if="formData.content">
        <h3 class="preview-section-title">Meeting Notes</h3>
        <div class="markdown-preview form-preview" v-html="formRenderedContent"></div>
      </div>
    </div>

    <form v-else @submit.prevent="handleCreate" class="meeting-form">
      <div class="form-group">
        <label for="meeting_id">Meeting ID *</label>
        <input
          id="meeting_id"
          v-model="formData.meeting_id"
          type="text"
          required
          placeholder="e.g., mtg-2026-01-05-kickoff"
        />
        <span class="form-hint">Unique identifier for this meeting. Use a consistent naming convention for meeting IDs: format: `{type}-{date}-{description}`</span>
      </div>

      <div class="form-row">
        <p class="form-hint org-project-hint">Choose an organization and/or a project — at least one is required.</p>
        <div class="form-group">
          <label for="org_id">Organization *</label>
          <select id="org_id" v-model="formData.org_id">
            <option :value="null">None</option>
            <option v-for="org in organizations" :key="org.id" :value="org.id">
              {{ org.name }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label for="project_id">Project *</label>
          <select id="project_id" v-model="formData.project_id">
            <option :value="null">None</option>
            <option v-for="project in filteredProjects" :key="project.id" :value="project.id">
              {{ project.name }}
            </option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <label for="presents">Attendees</label>
        <input
          id="presents"
          v-model="formData.presents"
          type="text"
          placeholder="e.g., John Doe, Jane Smith, Bob Wilson"
        />
        <span class="form-hint">Comma or semicolon separated</span>
      </div>

      <div class="form-group">
        <label>Meeting Notes (Markdown) *</label>
        <div class="markdown-editor-container">
          <div class="editor-tabs">
            <button type="button" :class="['tab-btn', { active: editorTab === 'write' }]" @click="editorTab = 'write'">Write</button>
            <button type="button" :class="['tab-btn', { active: editorTab === 'preview' }]" @click="editorTab = 'preview'">Preview</button>
          </div>
          <textarea
            v-if="editorTab === 'write'"
            v-model="formData.content"
            class="markdown-textarea"
            rows="15"
            required
            placeholder="# Meeting Title

## Agenda
1. Topic 1
2. Topic 2

## Notes
...

## Action Items
- [ ] Action 1
- [ ] Action 2
"
          />
          <div v-else class="markdown-preview form-preview" v-html="formRenderedContent"></div>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import { useMeetingRefStore } from '@/stores/meetingRefStore'

const router = useRouter()
const store = useMeetingRefStore()

const formData = ref({
  meeting_id: '',
  org_id: null,
  project_id: null,
  presents: '',
  content: ''
})

const editorTab = ref('write')
const fullPagePreview = ref(false)
const submitting = ref(false)

const organizations = computed(() => store.organizations)
const filteredProjects = computed(() => {
  if (!formData.value.org_id) return store.projects
  return store.projects.filter(p => p.organization_id === formData.value.org_id)
})

const hasOrgOrProject = computed(
  () => formData.value.org_id != null || formData.value.project_id != null
)

const isFormValid = computed(() => {
  return (
    formData.value.meeting_id &&
    formData.value.meeting_id.trim() &&
    hasOrgOrProject.value &&
    formData.value.content &&
    formData.value.content.trim()
  )
})

const formRenderedContent = computed(() => marked(formData.value.content || ''))

function getOrganizationName(orgId) {
  return store.getOrganizationName(orgId)
}

function getProjectName(projectId) {
  return store.getProjectName(projectId)
}

watch(() => formData.value.org_id, () => {
  formData.value.project_id = null
})

onMounted(async () => {
  await Promise.all([store.fetchOrganizations(), store.fetchProjects()])
})

async function handleCreate() {
  if (!isFormValid.value) return
  submitting.value = true
  try {
    const payload = {
      meeting_id: formData.value.meeting_id,
      org_id: formData.value.org_id,
      project_id: formData.value.project_id,
      content: formData.value.content,
      attendees: formData.value.presents?.trim() || null
    }
    const created = await store.createItem(payload)
    router.push({ name: 'MeetingEdit', params: { id: created.id } })
  } catch (err) {
    console.error('Failed to create meeting note:', err)
    alert('Failed to create meeting note: ' + (err.response?.data?.detail || err.message))
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.meeting-create-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .meeting-create-view {
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
  width: 100%;
  max-width: 100%;
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

.meeting-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  width: 100%;
  max-width: 100%;
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
}

:global(.dark) .form-group input,
:global(.dark) .form-group select {
  background: #1e293b;
  border-color: #334155;
  color: #f1f5f9;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-row .org-project-hint {
  grid-column: 1 / -1;
  margin: 0 0 0.25rem 0;
}

.form-hint {
  font-size: 0.75rem;
  color: #6b7280;
}

.markdown-editor-container {
  width: 100%;
  box-sizing: border-box;
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
  min-height: 200px;
  background: white;
}

:global(.dark) .markdown-textarea {
  background: #1e293b;
  color: #f1f5f9;
}

.markdown-preview.form-preview {
  padding: 0.75rem;
  min-height: 100px;
  max-height: 500px;
  overflow-y: auto;
  background: white;
}

:global(.dark) .markdown-preview.form-preview {
  background: #1e293b;
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
  .meeting-create-view {
    padding: 1rem;
  }
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>

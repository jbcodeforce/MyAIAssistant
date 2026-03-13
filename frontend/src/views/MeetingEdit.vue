<template>
  <div class="meeting-edit-view">
    <div class="view-header">
      <div class="header-left">
        <router-link to="/meetings" class="back-link">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
          Back to meeting notes
        </router-link>
        <h2 v-if="meeting">{{ meeting.meeting_id }}</h2>
        <h2 v-else-if="loading">Loading...</h2>
        <h2 v-else>Edit Meeting Note</h2>
      </div>
      <div class="header-actions" v-if="meeting">
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
          :disabled="saving"
        >
          Save
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading meeting note...</p>
    </div>

    <div v-else-if="loadError" class="error-state">
      <p>{{ loadError }}</p>
      <button @click="loadMeeting" class="btn-primary">Retry</button>
    </div>

    <div v-else-if="meeting && fullPagePreview" class="full-page-preview">
      <div class="preview-section">
        <h3 class="preview-section-title">Meeting ID</h3>
        <p class="preview-name">{{ meeting.meeting_id }}</p>
      </div>
      <div class="preview-section" v-if="meeting.org_id">
        <h3 class="preview-section-title">Organization</h3>
        <p class="preview-name">{{ getOrganizationName(meeting.org_id) }}</p>
      </div>
      <div class="preview-section" v-if="meeting.project_id">
        <h3 class="preview-section-title">Project</h3>
        <p class="preview-name">{{ getProjectName(meeting.project_id) }}</p>
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

    <form v-else-if="meeting" @submit.prevent="saveNow" class="meeting-form">
      <div class="form-group">
        <label>Meeting ID</label>
        <p class="read-only-value">{{ meeting.meeting_id }}</p>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label for="org_id">Organization</label>
          <select id="org_id" v-model="formData.org_id">
            <option :value="null">None</option>
            <option v-for="org in organizations" :key="org.id" :value="org.id">
              {{ org.name }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label for="project_id">Project</label>
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
          placeholder="e.g., John Doe, Jane Smith"
        />
        <span class="form-hint">Comma or semicolon separated</span>
      </div>

      <div class="form-group">
        <label>Meeting Notes (Markdown)</label>
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
            placeholder="# Meeting Title\n\n## Agenda\n..."
          />
          <div v-else class="markdown-preview form-preview" v-html="formRenderedContent"></div>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { useMeetingRefStore } from '@/stores/meetingRefStore'

const route = useRoute()
const store = useMeetingRefStore()

const meeting = ref(null)
const loading = ref(false)
const loadError = ref(null)

const formData = ref({
  org_id: null,
  project_id: null,
  presents: '',
  content: ''
})

const editorTab = ref('write')
const fullPagePreview = ref(false)
const saving = ref(false)
const lastSaveError = ref(null)
const lastSavedAt = ref(null)
const initialLoadDone = ref(false)

const DEBOUNCE_MS = 2500
let debounceTimer = null

const meetingId = computed(() => route.params.id)

const organizations = computed(() => store.organizations)
const filteredProjects = computed(() => {
  if (!formData.value.org_id) return store.projects
  return store.projects.filter(p => p.organization_id === formData.value.org_id)
})

const formRenderedContent = computed(() => marked(formData.value.content || ''))

function getOrganizationName(orgId) {
  return store.getOrganizationName(orgId)
}

function getProjectName(projectId) {
  return store.getProjectName(projectId)
}

async function loadMeeting() {
  const id = meetingId.value
  if (!id) {
    loadError.value = 'Missing meeting ID'
    return
  }
  loading.value = true
  loadError.value = null
  try {
    await Promise.all([store.fetchOrganizations(), store.fetchProjects()])
    const item = await store.getItem(id)
    meeting.value = item
    const contentResult = await store.getContent(id)
    formData.value = {
      org_id: item.org_id ?? null,
      project_id: item.project_id ?? null,
      presents: item.attendees || '',
      content: contentResult.content || ''
    }
    initialLoadDone.value = true
  } catch (err) {
    loadError.value = err.response?.data?.detail || 'Failed to load meeting note'
    console.error('Failed to load meeting:', err)
  } finally {
    loading.value = false
  }
}

function performSave() {
  if (!meeting.value) return
  saving.value = true
  lastSaveError.value = null
  store
    .updateItem(meeting.value.id, {
      org_id: formData.value.org_id,
      project_id: formData.value.project_id,
      attendees: formData.value.presents?.trim() || null,
      content: formData.value.content
    })
    .then(() => {
      lastSavedAt.value = new Date()
    })
    .catch((err) => {
      lastSaveError.value = err.response?.data?.detail || err.message
    })
    .finally(() => {
      saving.value = false
    })
}

function saveNow() {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
  performSave()
}

function debouncedSave() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    debounceTimer = null
    performSave()
  }, DEBOUNCE_MS)
}

watch(
  formData,
  () => {
    if (!initialLoadDone.value || !meeting.value) return
    debouncedSave()
  },
  { deep: true }
)

watch(meetingId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    initialLoadDone.value = false
    loadMeeting()
  }
})

onMounted(() => {
  loadMeeting()
})

function formatTime(date) {
  if (!date) return ''
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
</script>

<style scoped>
.meeting-edit-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .meeting-edit-view {
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

.meeting-form {
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

.read-only-value {
  margin: 0;
  padding: 0.5rem 0;
  font-size: 1rem;
  color: #6b7280;
  font-family: ui-monospace, monospace;
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
  .meeting-edit-view {
    padding: 1rem;
  }
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>

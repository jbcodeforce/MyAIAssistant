<template>
  <div class="meetings-view">
    <div class="view-header">
      <div>
        <h2>Meeting Notes</h2>
        <p class="view-description">
          Manage and track meeting notes with organization and project links
        </p>
      </div>
      <div class="header-actions">
        <div class="header-stats" v-if="!loading && !error">
          <span class="stat-badge total">{{ items.length }} meetings</span>
        </div>
        <button class="btn-primary" @click="openCreateModal">
          + New Meeting Note
        </button>
      </div>
    </div>

    <div class="filters-bar">
      <div class="filter-group">
        <label>Organization:</label>
        <select v-model="filterOrgId" @change="loadMeetings">
          <option value="">All Organizations</option>
          <option v-for="org in organizations" :key="org.id" :value="org.id">
            {{ org.name }}
          </option>
        </select>
      </div>
      <div class="filter-group">
        <label>Project:</label>
        <select v-model="filterProjectId" @change="loadMeetings">
          <option value="">All Projects</option>
          <option v-for="project in filteredProjects" :key="project.id" :value="project.id">
            {{ project.name }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading meeting notes...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadMeetings" class="btn-primary">Retry</button>
    </div>

    <div v-else class="meetings-content">
      <div v-if="items.length === 0" class="empty-state">
        <p>No meeting notes found</p>
        <p class="empty-state-hint">
          Create your first meeting note to get started
        </p>
      </div>

      <div v-else class="table-container">
        <table class="meetings-table">
          <thead>
            <tr>
              <th class="col-meeting-id">Meeting ID</th>
              <th class="col-org">Organization</th>
              <th class="col-project">Project</th>
              <th class="col-presents">Attendees</th>
              <th class="col-file">File Reference</th>
              <th class="col-date">Created</th>
              <th class="col-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in sortedItems" :key="item.id" class="meeting-row">
              <td class="col-meeting-id">
                <span class="meeting-id-badge">{{ item.meeting_id }}</span>
              </td>
              <td class="col-org">
                <span v-if="item.org_id" class="org-badge">
                  {{ getOrganizationName(item.org_id) }}
                </span>
                <span v-else class="no-value">-</span>
              </td>
              <td class="col-project">
                <span v-if="item.project_id" class="project-badge">
                  {{ getProjectName(item.project_id) }}
                </span>
                <span v-else class="no-value">-</span>
              </td>
              <td class="col-presents">
                <span v-if="item.presents" class="presents-text" :title="item.presents">
                  {{ truncate(item.presents, 30) }}
                </span>
                <span v-else class="no-value">-</span>
              </td>
              <td class="col-file">
                <span class="file-ref">{{ truncate(item.file_ref, 40) }}</span>
              </td>
              <td class="col-date">
                {{ formatDate(item.created_at) }}
              </td>
              <td class="col-actions">
                <button class="btn-icon" @click="openViewModal(item)" title="View Content">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                </button>
                <button class="btn-icon" @click="openEditModal(item)" title="Edit">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                    <path d="m15 5 4 4"/>
                  </svg>
                </button>
                <button class="btn-icon danger" @click="handleDelete(item)" title="Delete">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 6h18"/>
                    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                  </svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="hasMore" class="load-more">
        <button @click="loadMore" class="btn-secondary">
          Load More ({{ items.length }} of {{ totalCount }})
        </button>
      </div>
    </div>

    <!-- Create Modal -->
    <Modal :show="showCreateModal" title="New Meeting Note" size="fullscreen" @close="closeCreateModal">
      <form @submit.prevent="handleCreate" class="meeting-form">
        <div class="form-row">
          <div class="form-group">
            <label for="meeting_id">Meeting ID *</label>
            <input 
              id="meeting_id" 
              v-model="createFormData.meeting_id" 
              type="text" 
              required 
              placeholder="e.g., mtg-2026-01-05-kickoff"
            />
            <span class="form-hint">Unique identifier for this meeting</span>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="org_id">Organization</label>
            <select id="org_id" v-model="createFormData.org_id">
              <option :value="null">None</option>
              <option v-for="org in organizations" :key="org.id" :value="org.id">
                {{ org.name }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="project_id">Project</label>
            <select id="project_id" v-model="createFormData.project_id">
              <option :value="null">None</option>
              <option v-for="project in createFilteredProjects" :key="project.id" :value="project.id">
                {{ project.name }}
              </option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label for="presents">Attendees</label>
          <input 
            id="presents" 
            v-model="createFormData.presents" 
            type="text" 
            placeholder="e.g., John Doe, Jane Smith, Bob Wilson"
          />
          <span class="form-hint">Comma or semicolon separated list of meeting attendees</span>
        </div>

        <div class="form-group">
          <label>Meeting Notes (Markdown) *</label>
          <div class="markdown-editor-container">
            <div class="editor-tabs">
              <button 
                type="button" 
                :class="['tab-btn', { active: editorTab === 'write' }]"
                @click="editorTab = 'write'"
              >
                Write
              </button>
              <button 
                type="button" 
                :class="['tab-btn', { active: editorTab === 'preview' }]"
                @click="editorTab = 'preview'"
              >
                Preview
              </button>
            </div>
            <textarea 
              v-if="editorTab === 'write'"
              v-model="createFormData.content" 
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
            ></textarea>
            <div v-else class="markdown-preview" v-html="renderedCreateContent"></div>
          </div>
        </div>
      </form>

      <template #footer>
        <button type="button" class="btn-secondary" @click="closeCreateModal">Cancel</button>
        <button type="button" class="btn-primary" @click="handleCreate" :disabled="!isCreateFormValid">
          Create Meeting Note
        </button>
      </template>
    </Modal>

    <!-- View/Edit Modal -->
    <Modal :show="showEditModal" :title="isEditing ? 'Edit Meeting Note' : 'View Meeting Note'" size="fullscreen" @close="closeEditModal">
      <div v-if="loadingContent" class="loading-content">
        <p>Loading content...</p>
      </div>
      <div v-else>
        <div class="view-header-info" v-if="!isEditing">
          <div class="info-row">
            <span class="info-label">Meeting ID:</span>
            <span class="info-value">{{ editingItem?.meeting_id }}</span>
          </div>
          <div class="info-row" v-if="editingItem?.org_id">
            <span class="info-label">Organization:</span>
            <span class="info-value">{{ getOrganizationName(editingItem?.org_id) }}</span>
          </div>
          <div class="info-row" v-if="editingItem?.project_id">
            <span class="info-label">Project:</span>
            <span class="info-value">{{ getProjectName(editingItem?.project_id) }}</span>
          </div>
          <div class="info-row" v-if="editingItem?.presents">
            <span class="info-label">Attendees:</span>
            <span class="info-value">{{ editingItem?.presents }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">File:</span>
            <span class="info-value file-path">{{ editingItem?.file_ref }}</span>
          </div>
        </div>

        <form v-if="isEditing" @submit.prevent="handleUpdate" class="meeting-form">
          <div class="form-row">
            <div class="form-group">
              <label for="edit_org_id">Organization</label>
              <select id="edit_org_id" v-model="editFormData.org_id">
                <option :value="null">None</option>
                <option v-for="org in organizations" :key="org.id" :value="org.id">
                  {{ org.name }}
                </option>
              </select>
            </div>

            <div class="form-group">
              <label for="edit_project_id">Project</label>
              <select id="edit_project_id" v-model="editFormData.project_id">
                <option :value="null">None</option>
                <option v-for="project in editFilteredProjects" :key="project.id" :value="project.id">
                  {{ project.name }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label for="edit_presents">Attendees</label>
            <input 
              id="edit_presents" 
              v-model="editFormData.presents" 
              type="text" 
              placeholder="e.g., John Doe, Jane Smith, Bob Wilson"
            />
            <span class="form-hint">Comma or semicolon separated list of meeting attendees</span>
          </div>

          <div class="form-group">
            <label>Meeting Notes (Markdown)</label>
            <div class="markdown-editor-container">
              <div class="editor-tabs">
                <button 
                  type="button" 
                  :class="['tab-btn', { active: editEditorTab === 'write' }]"
                  @click="editEditorTab = 'write'"
                >
                  Write
                </button>
                <button 
                  type="button" 
                  :class="['tab-btn', { active: editEditorTab === 'preview' }]"
                  @click="editEditorTab = 'preview'"
                >
                  Preview
                </button>
              </div>
              <textarea 
                v-if="editEditorTab === 'write'"
                v-model="editFormData.content" 
                class="markdown-textarea"
                rows="15"
              ></textarea>
              <div v-else class="markdown-preview" v-html="renderedEditContent"></div>
            </div>
          </div>
        </form>

        <div v-else class="content-view">
          <div class="markdown-preview view-mode" v-html="renderedViewContent"></div>
        </div>
      </div>

      <template #footer>
        <button type="button" class="btn-secondary" @click="closeEditModal">
          {{ isEditing ? 'Cancel' : 'Close' }}
        </button>
        <button v-if="!isEditing" type="button" class="btn-primary" @click="startEditing">
          Edit
        </button>
        <button v-else type="button" class="btn-primary" @click="handleUpdate">
          Save Changes
        </button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { marked } from 'marked'
import { useMeetingRefStore } from '@/stores/meetingRefStore'
import Modal from '@/components/common/Modal.vue'

const store = useMeetingRefStore()

const items = ref([])
const totalCount = ref(0)
const currentSkip = ref(0)
const limit = 50
const loading = ref(false)
const error = ref(null)
const loadingContent = ref(false)

// Filters
const filterOrgId = ref('')
const filterProjectId = ref('')

// Create modal state
const showCreateModal = ref(false)
const editorTab = ref('write')
const createFormData = ref({
  meeting_id: '',
  org_id: null,
  project_id: null,
  presents: '',
  content: ''
})

// Edit/View modal state
const showEditModal = ref(false)
const isEditing = ref(false)
const editEditorTab = ref('write')
const editingItem = ref(null)
const viewContent = ref('')
const editFormData = ref({
  org_id: null,
  project_id: null,
  presents: '',
  content: ''
})

// Computed
const organizations = computed(() => store.organizations)
const projects = computed(() => store.projects)

const filteredProjects = computed(() => {
  if (!filterOrgId.value) return projects.value
  return projects.value.filter(p => p.organization_id === parseInt(filterOrgId.value))
})

const createFilteredProjects = computed(() => {
  if (!createFormData.value.org_id) return projects.value
  return projects.value.filter(p => p.organization_id === createFormData.value.org_id)
})

const editFilteredProjects = computed(() => {
  if (!editFormData.value.org_id) return projects.value
  return projects.value.filter(p => p.organization_id === editFormData.value.org_id)
})

const sortedItems = computed(() => {
  return [...items.value].sort((a, b) => {
    const dateA = new Date(a.created_at)
    const dateB = new Date(b.created_at)
    return dateB - dateA
  })
})

const hasMore = computed(() => {
  return items.value.length < totalCount.value
})

const isCreateFormValid = computed(() => {
  return createFormData.value.meeting_id && createFormData.value.content
})

const renderedCreateContent = computed(() => {
  return marked(createFormData.value.content || '')
})

const renderedEditContent = computed(() => {
  return marked(editFormData.value.content || '')
})

const renderedViewContent = computed(() => {
  return marked(viewContent.value || '')
})

// Watch for org changes to reset project
watch(() => createFormData.value.org_id, () => {
  createFormData.value.project_id = null
})

watch(() => editFormData.value.org_id, () => {
  editFormData.value.project_id = null
})

// Lifecycle
onMounted(async () => {
  await Promise.all([
    store.fetchOrganizations(),
    store.fetchProjects()
  ])
  await loadMeetings()
})

// Methods
async function loadMeetings() {
  loading.value = true
  error.value = null
  try {
    const params = { skip: 0, limit }
    if (filterOrgId.value) params.org_id = parseInt(filterOrgId.value)
    if (filterProjectId.value) params.project_id = parseInt(filterProjectId.value)
    
    const response = await store.fetchItems(params)
    items.value = response.meeting_refs
    totalCount.value = response.total
    currentSkip.value = response.meeting_refs.length
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load meeting notes'
    console.error('Failed to load meeting notes:', err)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  try {
    const params = { skip: currentSkip.value, limit }
    if (filterOrgId.value) params.org_id = parseInt(filterOrgId.value)
    if (filterProjectId.value) params.project_id = parseInt(filterProjectId.value)
    
    const response = await store.fetchItems(params)
    items.value = [...items.value, ...response.meeting_refs]
    currentSkip.value = items.value.length
  } catch (err) {
    console.error('Failed to load more items:', err)
  }
}

function getOrganizationName(orgId) {
  return store.getOrganizationName(orgId)
}

function getProjectName(projectId) {
  return store.getProjectName(projectId)
}

function openCreateModal() {
  createFormData.value = {
    meeting_id: '',
    org_id: null,
    project_id: null,
    presents: '',
    content: ''
  }
  editorTab.value = 'write'
  showCreateModal.value = true
}

function closeCreateModal() {
  showCreateModal.value = false
}

async function handleCreate() {
  if (!isCreateFormValid.value) return
  
  try {
    const created = await store.createItem(createFormData.value)
    items.value.unshift(created)
    totalCount.value++
    closeCreateModal()
  } catch (err) {
    console.error('Failed to create meeting note:', err)
    alert('Failed to create meeting note: ' + (err.response?.data?.detail || err.message))
  }
}

async function openViewModal(item) {
  editingItem.value = item
  isEditing.value = false
  showEditModal.value = true
  loadingContent.value = true
  
  try {
    const result = await store.getContent(item.id)
    viewContent.value = result.content
  } catch (err) {
    console.error('Failed to load content:', err)
    viewContent.value = '**Error loading content**'
  } finally {
    loadingContent.value = false
  }
}

async function openEditModal(item) {
  editingItem.value = item
  isEditing.value = true
  editEditorTab.value = 'write'
  showEditModal.value = true
  loadingContent.value = true
  
  try {
    const result = await store.getContent(item.id)
    editFormData.value = {
      org_id: item.org_id,
      project_id: item.project_id,
      presents: item.presents || '',
      content: result.content
    }
  } catch (err) {
    console.error('Failed to load content:', err)
    editFormData.value = {
      org_id: item.org_id,
      project_id: item.project_id,
      presents: item.presents || '',
      content: ''
    }
  } finally {
    loadingContent.value = false
  }
}

function startEditing() {
  isEditing.value = true
  editEditorTab.value = 'write'
  editFormData.value = {
    org_id: editingItem.value.org_id,
    project_id: editingItem.value.project_id,
    presents: editingItem.value.presents || '',
    content: viewContent.value
  }
}

function closeEditModal() {
  showEditModal.value = false
  editingItem.value = null
  isEditing.value = false
  viewContent.value = ''
}

async function handleUpdate() {
  try {
    const updated = await store.updateItem(editingItem.value.id, editFormData.value)
    const index = items.value.findIndex(i => i.id === editingItem.value.id)
    if (index !== -1) {
      items.value[index] = updated
    }
    closeEditModal()
  } catch (err) {
    console.error('Failed to update meeting note:', err)
    alert('Failed to update meeting note: ' + (err.response?.data?.detail || err.message))
  }
}

async function handleDelete(item) {
  if (confirm(`Delete meeting note "${item.meeting_id}"? This will also delete the file. This cannot be undone.`)) {
    try {
      await store.deleteItem(item.id)
      items.value = items.value.filter(i => i.id !== item.id)
      totalCount.value--
    } catch (err) {
      console.error('Failed to delete meeting note:', err)
      alert('Failed to delete meeting note: ' + (err.response?.data?.detail || err.message))
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

function truncate(text, maxLength) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}
</script>

<style scoped>
.meetings-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .meetings-view {
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

.stat-badge.total {
  background: #dbeafe;
  color: #1e40af;
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

.filter-group select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  background: white;
  cursor: pointer;
  min-width: 150px;
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

.meetings-content {
  width: 100%;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 12px;
  border: 2px dashed #e5e7eb;
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

.table-container {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  width: 100%;
}

:global(.dark) .table-container {
  background: #1e293b;
  border-color: #334155;
}

.meetings-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.meetings-table th {
  background: #f9fafb;
  padding: 0.875rem 1rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}

:global(.dark) .meetings-table th {
  background: #0f172a;
  color: #94a3b8;
  border-color: #334155;
}

.meetings-table td {
  padding: 0.875rem 1rem;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
}

:global(.dark) .meetings-table td {
  border-color: #334155;
}

.meetings-table tbody tr:last-child td {
  border-bottom: none;
}

.meetings-table tbody tr:hover {
  background: #f9fafb;
}

:global(.dark) .meetings-table tbody tr:hover {
  background: #0f172a;
}

.col-meeting-id {
  width: 200px;
}

.col-org,
.col-project {
  width: 150px;
}

.col-presents {
  width: 180px;
}

.col-file {
  min-width: 200px;
}

.col-date {
  width: 100px;
  white-space: nowrap;
}

.col-actions {
  width: 100px;
  text-align: center;
}

.meeting-id-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  background: #f3e8ff;
  color: #7c3aed;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 600;
  font-family: ui-monospace, monospace;
}

.org-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.project-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: #d1fae5;
  color: #065f46;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.file-ref {
  font-size: 0.75rem;
  color: #6b7280;
  font-family: ui-monospace, monospace;
}

.no-value {
  color: #d1d5db;
}

.presents-text {
  font-size: 0.8125rem;
  color: #4b5563;
}

:global(.dark) .presents-text {
  color: #9ca3af;
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

.btn-icon.danger:hover {
  background: #fee2e2;
  color: #dc2626;
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

.btn-secondary:hover {
  background-color: #f9fafb;
}

/* Form styles */
.meeting-form {
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

.form-group input,
.form-group select {
  padding: 0.625rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9375rem;
  transition: border-color 0.15s, box-shadow 0.15s;
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

.editor-tabs {
  display: flex;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.tab-btn {
  padding: 0.625rem 1rem;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border-bottom: 2px solid transparent;
}

.tab-btn:hover {
  color: #374151;
  background: rgba(0, 0, 0, 0.02);
}

.tab-btn.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
  background: white;
}

.markdown-textarea {
  width: 100%;
  padding: 1rem;
  border: none;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.9rem;
  line-height: 1.6;
  resize: vertical;
  min-height: 300px;
  background: white;
}

.markdown-textarea:focus {
  outline: none;
}

.markdown-textarea::placeholder {
  color: #9ca3af;
}

.markdown-preview {
  padding: 1rem;
  min-height: 300px;
  max-height: 500px;
  overflow-y: auto;
  background: white;
  line-height: 1.7;
}

.markdown-preview.view-mode {
  min-height: 400px;
  max-height: 600px;
}

.markdown-preview :deep(h1) {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.markdown-preview :deep(h2) {
  font-size: 1.375rem;
  font-weight: 600;
  margin: 1.5rem 0 0.75rem 0;
  color: #1e40af;
}

.markdown-preview :deep(h3) {
  font-size: 1.125rem;
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

.markdown-preview :deep(code) {
  background: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: ui-monospace, monospace;
  font-size: 0.875em;
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

.markdown-preview :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.markdown-preview :deep(th),
.markdown-preview :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 0.5rem 0.75rem;
  text-align: left;
}

.markdown-preview :deep(th) {
  background: #f9fafb;
  font-weight: 600;
}

/* View header info */
.view-header-info {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.info-row {
  display: flex;
  gap: 0.5rem;
  padding: 0.375rem 0;
}

.info-label {
  font-weight: 500;
  color: #6b7280;
  min-width: 100px;
}

.info-value {
  color: #111827;
}

.info-value.file-path {
  font-family: ui-monospace, monospace;
  font-size: 0.875rem;
  color: #6b7280;
}

.loading-content {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: #6b7280;
}

@media (max-width: 1024px) {
  .table-container {
    overflow-x: auto;
  }
  
  .meetings-table {
    min-width: 800px;
  }
}

@media (max-width: 768px) {
  .meetings-view {
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

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>


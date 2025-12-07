<template>
  <div class="knowledge-view">
    <div class="view-header">
      <div>
        <h2>Knowledge Base</h2>
        <p class="view-description">
          Manage referenced documents and web resources
        </p>
      </div>
      <div class="header-actions">
        <div class="header-stats" v-if="!loading && !error">
          <span class="stat-badge markdown">{{ markdownCount }} markdown</span>
          <span class="stat-badge website">{{ websiteCount }} website</span>
        </div>
        <button class="btn-primary" @click="openCreateModal">
          + Add Knowledge
        </button>
      </div>
    </div>

    <div class="filters-bar">
      <div class="filter-group">
        <label>Type:</label>
        <select v-model="filterType" @change="loadKnowledge">
          <option value="">All Types</option>
          <option value="markdown">Markdown</option>
          <option value="website">Website</option>
        </select>
      </div>
      <div class="filter-group">
        <label>Status:</label>
        <select v-model="filterStatus" @change="loadKnowledge">
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="pending">Pending</option>
          <option value="error">Error</option>
          <option value="archived">Archived</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading knowledge items...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadKnowledge" class="btn-primary">Retry</button>
    </div>

    <div v-else class="knowledge-content">
      <div v-if="items.length === 0" class="empty-state">
        <p>No knowledge items found</p>
        <p class="empty-state-hint">
          Add documents and web resources to build your knowledge base
        </p>
      </div>

      <div v-else class="table-container">
        <table class="knowledge-table">
          <thead>
            <tr>
              <th class="col-type">Type</th>
              <th class="col-title">Title</th>
              <th class="col-uri">URI</th>
              <th class="col-status">Status</th>
              <th class="col-date">Referenced</th>
              <th class="col-date">Last Fetched</th>
              <th class="col-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in sortedItems" :key="item.id" :class="['knowledge-row', item.status]">
              <td class="col-type">
                <span :class="['type-badge', item.document_type]">
                  {{ item.document_type }}
                </span>
              </td>
              <td class="col-title">
                <span class="item-title">{{ item.title }}</span>
                <span v-if="item.description" class="item-description">{{ truncate(item.description, 60) }}</span>
              </td>
              <td class="col-uri">
                <a v-if="isUrl(item.uri)" :href="item.uri" target="_blank" rel="noopener" class="uri-link">
                  {{ truncate(item.uri, 40) }}
                </a>
                <span v-else class="uri-text">{{ truncate(item.uri, 40) }}</span>
              </td>
              <td class="col-status">
                <span :class="['status-badge', item.status]">
                  {{ item.status }}
                </span>
              </td>
              <td class="col-date">{{ formatDate(item.referenced_at) }}</td>
              <td class="col-date">{{ item.last_fetched_at ? formatDate(item.last_fetched_at) : '-' }}</td>
              <td class="col-actions">
                <button class="btn-icon" @click="openEditModal(item)" title="Edit">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                    <path d="m15 5 4 4"/>
                  </svg>
                </button>
                <button class="btn-icon" @click="toggleArchive(item)" :title="item.status === 'archived' ? 'Restore' : 'Archive'">
                  <svg v-if="item.status === 'archived'" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                    <path d="M3 3v5h5"/>
                  </svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect width="20" height="5" x="2" y="3" rx="1"/>
                    <path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/>
                    <path d="M10 12h4"/>
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

    <!-- Create/Edit Modal -->
    <Modal :show="showModal" :title="isEditing ? 'Edit Knowledge' : 'Add Knowledge'" @close="closeModal">
      <form @submit.prevent="handleSubmit" class="knowledge-form">
        <div class="form-group">
          <label for="title">Title *</label>
          <input 
            id="title" 
            v-model="formData.title" 
            type="text" 
            required 
            placeholder="Enter a descriptive title"
          />
        </div>

        <div class="form-group">
          <label for="description">Description</label>
          <textarea 
            id="description" 
            v-model="formData.description" 
            rows="3"
            placeholder="Optional description of the knowledge item"
          ></textarea>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="document_type">Document Type *</label>
            <select id="document_type" v-model="formData.document_type" required>
              <option value="">Select type</option>
              <option value="markdown">Markdown</option>
              <option value="website">Website</option>
            </select>
          </div>

          <div class="form-group">
            <label for="status">Status</label>
            <select id="status" v-model="formData.status">
              <option value="active">Active</option>
              <option value="pending">Pending</option>
              <option value="error">Error</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label for="uri">URI *</label>
          <input 
            id="uri" 
            v-model="formData.uri" 
            type="text" 
            required 
            :placeholder="formData.document_type === 'website' ? 'https://example.com/docs' : 'file:///path/to/document.md'"
          />
          <span class="form-hint">File path or URL to the document</span>
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
import { useKnowledgeStore } from '@/stores/knowledgeStore'
import Modal from '@/components/common/Modal.vue'

const knowledgeStore = useKnowledgeStore()

const items = ref([])
const totalCount = ref(0)
const currentSkip = ref(0)
const limit = 50
const loading = ref(false)
const error = ref(null)

// Filters
const filterType = ref('')
const filterStatus = ref('')

// Modal state
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const formData = ref({
  title: '',
  description: '',
  document_type: '',
  uri: '',
  status: 'active'
})

const sortedItems = computed(() => {
  return [...items.value].sort((a, b) => {
    const dateA = new Date(a.created_at)
    const dateB = new Date(b.created_at)
    return dateB - dateA
  })
})

const markdownCount = computed(() => {
  return items.value.filter(item => item.document_type === 'markdown').length
})

const websiteCount = computed(() => {
  return items.value.filter(item => item.document_type === 'website').length
})

const hasMore = computed(() => {
  return items.value.length < totalCount.value
})

const isFormValid = computed(() => {
  return formData.value.title && formData.value.document_type && formData.value.uri
})

onMounted(() => {
  loadKnowledge()
})

async function loadKnowledge() {
  loading.value = true
  error.value = null
  try {
    const params = { skip: 0, limit }
    if (filterType.value) params.document_type = filterType.value
    if (filterStatus.value) params.status = filterStatus.value
    
    const response = await knowledgeStore.fetchItems(params)
    items.value = response.items
    totalCount.value = response.total
    currentSkip.value = response.items.length
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load knowledge items'
    console.error('Failed to load knowledge items:', err)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  try {
    const params = { skip: currentSkip.value, limit }
    if (filterType.value) params.document_type = filterType.value
    if (filterStatus.value) params.status = filterStatus.value
    
    const response = await knowledgeStore.fetchItems(params)
    items.value = [...items.value, ...response.items]
    currentSkip.value = items.value.length
  } catch (err) {
    console.error('Failed to load more items:', err)
  }
}

function openCreateModal() {
  isEditing.value = false
  editingId.value = null
  formData.value = {
    title: '',
    description: '',
    document_type: '',
    uri: '',
    status: 'active'
  }
  showModal.value = true
}

function openEditModal(item) {
  isEditing.value = true
  editingId.value = item.id
  formData.value = {
    title: item.title,
    description: item.description || '',
    document_type: item.document_type,
    uri: item.uri,
    status: item.status
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  isEditing.value = false
  editingId.value = null
}

async function handleSubmit() {
  if (!isFormValid.value) return
  
  try {
    if (isEditing.value) {
      const updated = await knowledgeStore.updateItem(editingId.value, formData.value)
      const index = items.value.findIndex(item => item.id === editingId.value)
      if (index !== -1) {
        items.value[index] = updated
      }
    } else {
      const created = await knowledgeStore.createItem(formData.value)
      items.value.unshift(created)
      totalCount.value++
    }
    closeModal()
  } catch (err) {
    console.error('Failed to save knowledge item:', err)
  }
}

async function toggleArchive(item) {
  const newStatus = item.status === 'archived' ? 'active' : 'archived'
  const action = item.status === 'archived' ? 'restore' : 'archive'
  
  if (confirm(`Are you sure you want to ${action} "${item.title}"?`)) {
    try {
      const updated = await knowledgeStore.updateItem(item.id, { status: newStatus })
      const index = items.value.findIndex(i => i.id === item.id)
      if (index !== -1) {
        items.value[index] = updated
      }
    } catch (err) {
      console.error(`Failed to ${action} item:`, err)
    }
  }
}

async function handleDelete(item) {
  if (confirm(`Permanently delete "${item.title}"? This cannot be undone.`)) {
    try {
      await knowledgeStore.deleteItem(item.id)
      items.value = items.value.filter(i => i.id !== item.id)
      totalCount.value--
    } catch (err) {
      console.error('Failed to delete item:', err)
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

function isUrl(uri) {
  return uri.startsWith('http://') || uri.startsWith('https://')
}
</script>

<style scoped>
.knowledge-view {
  min-height: calc(100vh - 80px);
  background: #f9fafb;
  padding: 2rem;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  max-width: 1400px;
  margin-left: auto;
  margin-right: auto;
}

.view-header h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
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

.stat-badge.markdown {
  background: #dbeafe;
  color: #1e40af;
}

.stat-badge.website {
  background: #fef3c7;
  color: #92400e;
}

.filters-bar {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  max-width: 1400px;
  margin-left: auto;
  margin-right: auto;
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

.knowledge-content {
  max-width: 1400px;
  margin: 0 auto;
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
}

.knowledge-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.knowledge-table th {
  background: #f9fafb;
  padding: 0.875rem 1rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}

.knowledge-table td {
  padding: 0.875rem 1rem;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
}

.knowledge-table tbody tr:last-child td {
  border-bottom: none;
}

.knowledge-table tbody tr:hover {
  background: #f9fafb;
}

.knowledge-row.archived {
  background: #f3f4f6;
  opacity: 0.8;
}

.knowledge-row.error {
  background: #fef2f2;
}

.knowledge-row.pending {
  background: #fffbeb;
}

.col-type {
  width: 100px;
}

.col-title {
  min-width: 200px;
}

.col-uri {
  min-width: 200px;
  max-width: 300px;
}

.col-status {
  width: 90px;
}

.col-date {
  width: 110px;
  white-space: nowrap;
}

.col-actions {
  width: 110px;
  text-align: center;
}

.type-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.type-badge.markdown {
  background: #dbeafe;
  color: #1e40af;
}

.type-badge.website {
  background: #fef3c7;
  color: #92400e;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.status-badge.active {
  background: #dcfce7;
  color: #166534;
}

.status-badge.pending {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.error {
  background: #fee2e2;
  color: #991b1b;
}

.status-badge.archived {
  background: #f3f4f6;
  color: #6b7280;
}

.item-title {
  display: block;
  font-weight: 500;
  color: #111827;
}

.item-description {
  display: block;
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

.uri-link {
  color: #2563eb;
  text-decoration: none;
  font-size: 0.8125rem;
}

.uri-link:hover {
  text-decoration: underline;
}

.uri-text {
  color: #6b7280;
  font-size: 0.8125rem;
  font-family: ui-monospace, monospace;
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
.knowledge-form {
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
.form-group textarea,
.form-group select {
  padding: 0.625rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9375rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
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

@media (max-width: 1024px) {
  .table-container {
    overflow-x: auto;
  }
  
  .knowledge-table {
    min-width: 900px;
  }
}

@media (max-width: 768px) {
  .knowledge-view {
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


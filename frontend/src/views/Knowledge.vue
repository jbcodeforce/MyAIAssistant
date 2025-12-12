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
        <button 
          class="btn-chat" 
          @click="showChatModal = true"
          title="Chat with Knowledge Base"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          Ask AI
        </button>
        <button 
          class="btn-secondary index-all-btn" 
          @click="handleIndexAll"
          :disabled="indexingAll || items.length === 0"
        >
          <svg v-if="indexingAll" class="spinner" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.3-4.3"/>
            <path d="M11 8v6"/>
            <path d="M8 11h6"/>
          </svg>
          {{ indexingAll ? 'Indexing...' : 'Index All' }}
        </button>
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
      <div class="filter-group">
        <label>Category:</label>
        <select v-model="filterCategory" @change="loadKnowledge">
          <option value="">All Categories</option>
          <option v-for="cat in availableCategories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>Tag:</label>
        <input 
          v-model="filterTag" 
          type="text" 
          placeholder="Filter by tag..."
          @keyup.enter="loadKnowledge"
          class="tag-filter-input"
        />
        <button v-if="filterTag" class="btn-clear" @click="filterTag = ''; loadKnowledge()" title="Clear">
          &times;
        </button>
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
              <th class="col-category">Category</th>
              <th class="col-tags">Tags</th>
              <th class="col-status">Status</th>
              <th class="col-date">Indexed</th>
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
                <span v-if="item.description" class="item-description">{{ truncate(item.description, 50) }}</span>
                <span class="item-uri">{{ truncate(item.uri, 35) }}</span>
              </td>
              <td class="col-category">
                <span v-if="item.category" class="category-badge">{{ item.category }}</span>
                <span v-else class="no-value">-</span>
              </td>
              <td class="col-tags">
                <div v-if="item.tags" class="tags-list">
                  <span 
                    v-for="tag in item.tags.split(',')" 
                    :key="tag" 
                    class="tag-badge"
                    @click="filterByTag(tag)"
                  >
                    {{ tag }}
                  </span>
                </div>
                <span v-else class="no-value">-</span>
              </td>
              <td class="col-status">
                <span :class="['status-badge', item.status]">
                  {{ item.status }}
                </span>
              </td>
              <td class="col-date">
                <span v-if="item.indexed_at">{{ formatDate(item.indexed_at) }}</span>
                <span v-else class="not-indexed">Not yet</span>
              </td>
              <td class="col-actions">
                <button 
                  class="btn-icon index-btn" 
                  @click="handleIndex(item)" 
                  :title="isIndexing(item.id) ? 'Indexing...' : 'Index for RAG'"
                  :disabled="isIndexing(item.id)"
                  :class="{ indexing: isIndexing(item.id) }"
                >
                  <svg v-if="isIndexing(item.id)" class="spinner" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                  </svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="11" cy="11" r="8"/>
                    <path d="m21 21-4.3-4.3"/>
                    <path d="M11 8v6"/>
                    <path d="M8 11h6"/>
                  </svg>
                </button>
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

        <div class="form-row">
          <div class="form-group">
            <label for="category">Category</label>
            <input 
              id="category" 
              v-model="formData.category" 
              type="text" 
              list="category-suggestions"
              placeholder="e.g., Documentation, Reference, Tutorial"
            />
            <datalist id="category-suggestions">
              <option v-for="cat in availableCategories" :key="cat" :value="cat" />
            </datalist>
          </div>

          <div class="form-group">
            <label for="tags">Tags</label>
            <input 
              id="tags" 
              v-model="formData.tags" 
              type="text" 
              placeholder="Comma-separated: python, api, backend"
            />
            <span class="form-hint">Separate multiple tags with commas</span>
          </div>
        </div>

        <div class="form-group">
          <label>Source *</label>
          
          <!-- Source type toggle for markdown -->
          <div v-if="formData.document_type === 'markdown'" class="source-toggle">
            <button 
              type="button" 
              :class="['toggle-btn', { active: sourceMode === 'file' }]"
              @click="sourceMode = 'file'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
                <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
              </svg>
              File
            </button>
            <button 
              type="button" 
              :class="['toggle-btn', { active: sourceMode === 'url' }]"
              @click="sourceMode = 'url'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
              URL
            </button>
          </div>

          <!-- Local file path input -->
          <div v-if="formData.document_type === 'markdown' && sourceMode === 'file'">
            <div class="file-path-input">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
                <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
              </svg>
              <input 
                v-model="formData.uri" 
                type="text" 
                required 
                placeholder="/Users/username/Documents/notes.md"
                @blur="normalizeFilePath"
              />
            </div>
            <span class="form-hint">Enter the absolute path to the markdown file (e.g., /home/user/docs/readme.md)</span>
          </div>

          <!-- URL input for markdown -->
          <div v-else-if="formData.document_type === 'markdown' && sourceMode === 'url'">
            <input 
              id="uri" 
              v-model="formData.uri" 
              type="text" 
              required 
              placeholder="https://example.com/document.md or file:///path/to/document.md"
            />
            <span class="form-hint">Enter a URL or file path to the markdown document</span>
          </div>

          <!-- URL input for website (always shown) -->
          <div v-else-if="formData.document_type === 'website'">
            <input 
              id="uri" 
              v-model="formData.uri" 
              type="url" 
              required 
              placeholder="https://example.com/docs"
            />
            <span class="form-hint">Enter the website URL to scrape</span>
          </div>

          <!-- Placeholder when no type selected -->
          <div v-else>
            <input 
              type="text" 
              disabled 
              placeholder="Select a document type first"
              class="disabled-input"
            />
          </div>
        </div>
      </form>

      <template #footer>
        <button type="button" class="btn-secondary" @click="closeModal">Cancel</button>
        <button type="button" class="btn-primary" @click="handleSubmit" :disabled="!isFormValid">
          {{ isEditing ? 'Update' : 'Create' }}
        </button>
      </template>
    </Modal>

    <!-- RAG Chat Modal -->
    <RagChatModal 
      :show="showChatModal" 
      @close="showChatModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useKnowledgeStore } from '@/stores/knowledgeStore'
import { ragApi } from '@/services/api'
import Modal from '@/components/common/Modal.vue'
import RagChatModal from '@/components/chat/RagChatModal.vue'

const knowledgeStore = useKnowledgeStore()

const items = ref([])
const totalCount = ref(0)
const currentSkip = ref(0)
const limit = 50
const loading = ref(false)
const error = ref(null)
const indexingItems = ref(new Set()) // Track items currently being indexed
const indexingAll = ref(false) // Track bulk indexing state

// Filters
const filterType = ref('')
const filterStatus = ref('')
const filterCategory = ref('')
const filterTag = ref('')

// Modal state
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const showChatModal = ref(false)
const formData = ref({
  title: '',
  description: '',
  document_type: '',
  uri: '',
  category: '',
  tags: '',
  status: 'active'
})

// Computed available categories from items
const availableCategories = computed(() => {
  const categories = new Set()
  items.value.forEach(item => {
    if (item.category) categories.add(item.category)
  })
  return Array.from(categories).sort()
})

// Source mode state
const sourceMode = ref('file') // 'file' or 'url'

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
    if (filterCategory.value) params.category = filterCategory.value
    if (filterTag.value) params.tag = filterTag.value.trim()
    
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
    if (filterCategory.value) params.category = filterCategory.value
    if (filterTag.value) params.tag = filterTag.value.trim()
    
    const response = await knowledgeStore.fetchItems(params)
    items.value = [...items.value, ...response.items]
    currentSkip.value = items.value.length
  } catch (err) {
    console.error('Failed to load more items:', err)
  }
}

function filterByTag(tag) {
  filterTag.value = tag.trim()
  loadKnowledge()
}

function openCreateModal() {
  isEditing.value = false
  editingId.value = null
  formData.value = {
    title: '',
    description: '',
    document_type: '',
    uri: '',
    category: '',
    tags: '',
    status: 'active'
  }
  sourceMode.value = 'file'
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
    category: item.category || '',
    tags: item.tags || '',
    status: item.status
  }
  // Determine source mode based on existing URI
  if (item.document_type === 'markdown') {
    sourceMode.value = isUrl(item.uri) ? 'url' : 'file'
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
  
  // Ensure file:// prefix for local file paths
  normalizeFilePath()
  
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

async function handleIndex(item) {
  if (indexingItems.value.has(item.id)) return
  
  indexingItems.value.add(item.id)
  
  try {
    const response = await ragApi.indexItem(item.id)
    const result = response.data
    
    if (result.success) {
      // Update the item with new content_hash and last_fetched_at
      const index = items.value.findIndex(i => i.id === item.id)
      if (index !== -1) {
        items.value[index] = {
          ...items.value[index],
          content_hash: result.content_hash,
          status: 'active'
        }
      }
      alert(`Successfully indexed "${item.title}" (${result.chunks_indexed} chunks)`)
    } else {
      alert(`Failed to index "${item.title}": ${result.error}`)
      // Update status to error
      const index = items.value.findIndex(i => i.id === item.id)
      if (index !== -1) {
        items.value[index] = { ...items.value[index], status: 'error' }
      }
    }
  } catch (err) {
    console.error('Failed to index item:', err)
    alert(`Failed to index "${item.title}": ${err.response?.data?.detail || err.message}`)
  } finally {
    indexingItems.value.delete(item.id)
  }
}

function isIndexing(itemId) {
  return indexingItems.value.has(itemId)
}

async function handleIndexAll() {
  if (indexingAll.value || items.value.length === 0) return
  
  const activeItems = items.value.filter(i => i.status === 'active' || i.status === 'pending')
  if (activeItems.length === 0) {
    alert('No active items to index')
    return
  }
  
  if (!confirm(`Index ${activeItems.length} active/pending items into the RAG system?`)) {
    return
  }
  
  indexingAll.value = true
  
  try {
    const response = await ragApi.indexAll('active,pending')
    const result = response.data
    
    // Refresh the list to get updated statuses
    await loadKnowledge()
    
    alert(`Indexing complete: ${result.successful} succeeded, ${result.failed} failed`)
  } catch (err) {
    console.error('Failed to index all items:', err)
    alert(`Failed to index items: ${err.response?.data?.detail || err.message}`)
  } finally {
    indexingAll.value = false
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

function normalizeFilePath() {
  // Ensure the path starts with file:// for local files (only for markdown + file mode)
  if (formData.value.document_type !== 'markdown' || sourceMode.value !== 'file') {
    return
  }
  
  let path = formData.value.uri
  if (path && !path.startsWith('file://') && !path.startsWith('http://') && !path.startsWith('https://')) {
    // It's a local path, add file:// prefix
    formData.value.uri = `file://${path}`
  }
}
</script>

<style scoped>
.knowledge-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .knowledge-view {
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

.btn-chat {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-chat:hover {
  background: #059669;
}

.btn-chat svg {
  flex-shrink: 0;
}

.index-all-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #f3e8ff;
  color: #7c3aed;
  border: 1px solid #ddd6fe;
}

.index-all-btn:hover:not(:disabled) {
  background: #ede9fe;
  border-color: #c4b5fd;
}

.index-all-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.index-all-btn svg {
  flex-shrink: 0;
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
}

.filter-group select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.tag-filter-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  width: 140px;
}

.tag-filter-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.btn-clear {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0 0.25rem;
  line-height: 1;
}

.btn-clear:hover {
  color: #111827;
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
  width: 90px;
}

.col-title {
  min-width: 180px;
}

.col-category {
  width: 120px;
}

.col-tags {
  min-width: 140px;
  max-width: 200px;
}

.col-status {
  width: 80px;
}

.col-date {
  width: 100px;
  white-space: nowrap;
}

.col-actions {
  width: 100px;
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

.item-uri {
  display: block;
  font-size: 0.7rem;
  color: #9ca3af;
  margin-top: 0.25rem;
  font-family: ui-monospace, monospace;
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

.category-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.tag-badge {
  display: inline-block;
  padding: 0.125rem 0.375rem;
  background: #f3f4f6;
  color: #4b5563;
  border-radius: 4px;
  font-size: 0.6875rem;
  cursor: pointer;
  transition: all 0.15s;
}

.tag-badge:hover {
  background: #2563eb;
  color: white;
}

.no-value {
  color: #d1d5db;
}

.not-indexed {
  color: #9ca3af;
  font-style: italic;
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

.btn-icon.index-btn {
  color: #8b5cf6;
}

.btn-icon.index-btn:hover {
  background: #f3e8ff;
  color: #7c3aed;
}

.btn-icon.index-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.btn-icon.index-btn.indexing {
  color: #8b5cf6;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
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

/* Source toggle styles */
.source-toggle {
  display: flex;
  gap: 0;
  margin-bottom: 0.75rem;
  background: #f3f4f6;
  border-radius: 8px;
  padding: 4px;
  width: fit-content;
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.15s;
}

.toggle-btn:hover {
  color: #374151;
}

.toggle-btn.active {
  background: white;
  color: #2563eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* File path input styles */
.file-path-input {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.file-path-input:focus-within {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.file-path-input svg {
  color: #6b7280;
  flex-shrink: 0;
}

.file-path-input input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 0.9375rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  background: transparent;
}

.file-path-input input::placeholder {
  font-family: inherit;
  color: #9ca3af;
}

/* Legacy file input styles - kept for compatibility */
.file-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.file-input-display {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  background: #fafafa;
}

.file-input-display:hover {
  border-color: #2563eb;
  background: #f0f7ff;
}

.file-input-display svg {
  color: #6b7280;
  flex-shrink: 0;
}

.file-input-display:hover svg {
  color: #2563eb;
}

.file-input-display span {
  font-size: 0.9375rem;
  color: #111827;
}

.file-input-display .placeholder {
  color: #9ca3af;
}

.disabled-input {
  background: #f3f4f6 !important;
  cursor: not-allowed;
  color: #9ca3af !important;
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


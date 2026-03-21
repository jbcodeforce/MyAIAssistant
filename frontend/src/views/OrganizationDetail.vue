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
        <router-link
          :to="{ name: 'OrganizationEdit', params: { id: organization.id } }"
          class="btn-secondary"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
            <path d="m15 5 4 4"/>
          </svg>
          Edit
        </router-link>
        <router-link 
          :to="{ path: '/projects', query: { organization: organization.id } }" 
          class="btn-primary"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
          View Projects
        </router-link>
        <router-link
          :to="{ name: 'Meetings', query: { organization: organization.id } }"
          class="btn-primary"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>
            <line x1="16" x2="16" y1="2" y2="6"/>
            <line x1="8" x2="8" y1="2" y2="6"/>
            <line x1="3" x2="21" y1="10" y2="10"/>
          </svg>
          Meeting notes
        </router-link>
        <router-link 
          :to="`/organizations/${organization.id}/todos`" 
          class="btn-primary"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 5H2v7l6.29 6.29c.94.94 2.48.94 3.42 0l3.58-3.58c.94-.94.94-2.48 0-3.42L9 5Z"/>
            <path d="M6 9.01V9"/>
          </svg>
          View Tasks
        </router-link>
        <button
          type="button"
          class="btn-secondary"
          :disabled="exporting"
          @click="handleExport"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          {{ exporting ? 'Exporting...' : 'Export' }}
        </button>
      </div>
    </div>

    <div v-if="exportMessage" class="export-message" :class="exportError ? 'error' : 'success'">
      {{ exportMessage }}
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
        <router-link
          :to="{ name: 'OrganizationEdit', params: { id: organization.id } }"
          class="btn-primary"
        >
          Add Content
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { organizationsApi } from '@/services/api'

const route = useRoute()

const organization = ref(null)
const loading = ref(false)
const error = ref(null)
const exporting = ref(false)
const exportMessage = ref('')
const exportError = ref(false)

// Computed for rendered markdown (view mode)
const renderedStakeholders = computed(() => marked(organization.value?.stakeholders || ''))
const renderedTeam = computed(() => marked(organization.value?.team || ''))
const renderedDescription = computed(() => marked(organization.value?.description || ''))
const renderedProducts = computed(() => marked(organization.value?.related_products || ''))

const hasContent = computed(() => {
  if (!organization.value) return false
  return organization.value.stakeholders || 
         organization.value.team || 
         organization.value.description || 
         organization.value.related_products
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

async function handleExport() {
  if (!organization.value || exporting.value) return
  exporting.value = true
  exportMessage.value = ''
  exportError.value = false
  try {
    const response = await organizationsApi.export(organization.value.id)
    const path = response.data?.path || 'docs/.../index.md'
    exportMessage.value = `Exported to ${path}`
    exportError.value = false
    setTimeout(() => { exportMessage.value = '' }, 5000)
  } catch (err) {
    exportMessage.value = err.response?.data?.detail || 'Export failed'
    exportError.value = true
    setTimeout(() => { exportMessage.value = '' }, 5000)
  } finally {
    exporting.value = false
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

.export-message {
  margin-bottom: 1rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
}

.export-message.success {
  background: #d1fae5;
  color: #065f46;
}

.export-message.error {
  background: #fee2e2;
  color: #991b1b;
}

:global(.dark) .export-message.success {
  background: #064e3b;
  color: #6ee7b7;
}

:global(.dark) .export-message.error {
  background: #7f1d1d;
  color: #fca5a5;
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

.markdown-preview :deep(ul) {
  list-style-type: disc;
  list-style-position: outside;
  padding-left: 1.5rem;
  margin: 0 0 1rem 0;
}

.markdown-preview :deep(ol) {
  list-style-type: decimal;
  list-style-position: outside;
  padding-left: 1.5rem;
  margin: 0 0 1rem 0;
}

.markdown-preview :deep(li) {
  display: list-item;
  margin: 0.25rem 0;
}

.markdown-preview :deep(strong) {
  font-weight: 600;
}

.markdown-preview :deep(a) {
  color: #2563eb;
  text-decoration: underline;
  cursor: pointer;
}

.markdown-preview :deep(a:hover) {
  color: #1d4ed8;
}

:global(.dark) .markdown-preview :deep(a) {
  color: #60a5fa;
}

:global(.dark) .markdown-preview :deep(a:hover) {
  color: #93c5fd;
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



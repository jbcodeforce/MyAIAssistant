<template>
  <div class="organizations-view">
    <div class="view-header">
      <div>
        <h2>Organizations</h2>
        <p class="view-description">
          Manage organization profiles, stakeholders, and strategy information. (Drag&Drop to Top active section)
        </p>
      </div>
      <div class="header-actions">
        <span class="organization-count" v-if="!loading && !error">
          {{ totalCount }} organization{{ totalCount !== 1 ? 's' : '' }}
        </span>
        <router-link to="/organizations/new" class="btn-primary">
          + New Organization
        </router-link>
      </div>
    </div>

    <div class="search-bar" v-if="!loading && !error">
      <div class="search-input-wrapper">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="search-icon">
          <circle cx="11" cy="11" r="8"/>
          <path d="m21 21-4.3-4.3"/>
        </svg>
        <input 
          v-model="searchQuery"
          type="text"
          placeholder="Search organizations..."
          class="search-input"
        />
        <button 
          v-if="searchQuery"
          class="clear-search"
          @click="searchQuery = ''"
          title="Clear search"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 6 6 18"/>
            <path d="m6 6 12 12"/>
          </svg>
        </button>
      </div>
      <span v-if="searchQuery && filteredOrganizations.length !== organizations.length" class="search-results-count">
        {{ filteredOrganizations.length }} of {{ organizations.length }} shown
      </span>
      <div class="view-toggle">
        <button
          type="button"
          :class="['toggle-btn', { active: viewMode === 'tiles' }]"
          @click="setViewMode('tiles')"
          title="Tile view"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect width="7" height="7" x="3" y="3" rx="1"/>
            <rect width="7" height="7" x="14" y="3" rx="1"/>
            <rect width="7" height="7" x="14" y="14" rx="1"/>
            <rect width="7" height="7" x="3" y="14" rx="1"/>
          </svg>
          Tiles
        </button>
        <button
          type="button"
          :class="['toggle-btn', { active: viewMode === 'table' }]"
          @click="setViewMode('table')"
          title="Table view"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 3v18"/>
            <rect width="18" height="18" x="3" y="3" rx="2"/>
            <path d="M3 9h18"/>
            <path d="M3 15h18"/>
          </svg>
          Table
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

      <div v-else-if="filteredOrganizations.length === 0" class="empty-state">
        <p>No organizations match "{{ searchQuery }}"</p>
        <p class="empty-state-hint">
          Try a different search term
        </p>
      </div>

      <div v-else-if="viewMode === 'tiles'" class="organizations-grid">
        <div 
          v-for="organization in filteredOrganizations" 
          :key="organization.id" 
          class="organization-card"
          draggable="true"
          @dragstart="onOrgDragStart($event, organization)"
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
              <router-link 
                :to="`/organizations/${organization.id}`" 
                class="btn-icon" 
                title="View"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              </router-link>
              <button class="btn-icon" @click="goToEdit(organization)" title="Edit">
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
            <router-link 
              :to="`/organizations/${organization.id}/todos`" 
              class="view-projects-link"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 5H2v7l6.29 6.29c.94.94 2.48.94 3.42 0l3.58-3.58c.94-.94.94-2.48 0-3.42L9 5Z"/>
                <path d="M6 9.01V9"/>
              </svg>
              View Tasks
            </router-link>
            <router-link 
              :to="{ path: '/meetings', query: { organization: organization.id } }" 
              class="view-projects-link"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>
                <path d="M16 2v4"/>
                <path d="M8 2v4"/>
                <path d="M3 10h18"/>
              </svg>
              View Meetings
            </router-link>
          </div>
        </div>
      </div>

      <div v-else class="table-container">
        <table class="organizations-table">
          <thead>
            <tr>
              <th class="col-name">Name</th>
              <th class="col-created">Created</th>
              <th class="col-sections">Sections</th>
              <th class="col-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="organization in filteredOrganizations"
              :key="organization.id"
              class="org-row"
              draggable="true"
              @dragstart="onOrgDragStart($event, organization)"
            >
              <td class="col-name">
                <div class="table-org-name">
                  <span class="organization-avatar table-avatar">{{ getInitials(organization.name) }}</span>
                  <router-link :to="`/organizations/${organization.id}`" class="org-name-link">
                    {{ organization.name }}
                  </router-link>
                </div>
              </td>
              <td class="col-created">{{ formatDate(organization.created_at) }}</td>
              <td class="col-sections">
                <span class="sections-summary">{{ getSectionsSummary(organization) }}</span>
              </td>
              <td class="col-actions">
                <router-link :to="`/organizations/${organization.id}`" class="btn-icon" title="View">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                </router-link>
                <button type="button" class="btn-icon" @click="goToEdit(organization)" title="Edit">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                    <path d="m15 5 4 4"/>
                  </svg>
                </button>
                <button type="button" class="btn-icon danger" @click="handleDelete(organization)" title="Delete">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 6h18"/>
                    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                  </svg>
                </button>
                <router-link :to="{ path: '/projects', query: { organization: organization.id } }" class="btn-icon" title="View Projects">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                  </svg>
                </router-link>
                <router-link :to="`/organizations/${organization.id}/todos`" class="btn-icon" title="View Tasks">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 5H2v7l6.29 6.29c.94.94 2.48.94 3.42 0l3.58-3.58c.94-.94.94-2.48 0-3.42L9 5Z"/>
                    <path d="M6 9.01V9"/>
                  </svg>
                </router-link>
                <router-link :to="{ path: '/meetings', query: { organization: organization.id } }" class="btn-icon" title="View Meetings">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>
                    <path d="M16 2v4"/>
                    <path d="M8 2v4"/>
                    <path d="M3 10h18"/>
                  </svg>
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="hasMore" class="load-more">
        <button @click="loadMore" class="btn-secondary">
          Load More ({{ organizations.length }} of {{ totalCount }})
        </button>
      </div>

      <!-- Top active organizations -->
      <section v-if="!loading && !error" class="top-active-section">
        <h3 class="top-active-heading">Top active organizations</h3>
        <div
          class="top-active-drop-zone"
          :class="{ 'drag-over': topActiveDragOver }"
          @dragover.prevent="topActiveDragOver = true"
          @dragleave.prevent="topActiveDragOver = false"
          @drop.prevent="onTopActiveDrop"
        >
          <table v-if="topActiveOrganizations.length > 0" class="top-active-table">
            <thead>
              <tr>
                <th class="col-name">Name</th>
                <th class="col-actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="org in topActiveOrganizations" :key="org.id">
                <td class="col-name">
                  <span class="organization-avatar table-avatar">{{ getInitials(org.name) }}</span>
                  <router-link :to="`/organizations/${org.id}`" class="org-name-link">{{ org.name }}</router-link>
                </td>
                <td class="col-actions">
                  <router-link :to="`/organizations/${org.id}`" class="btn-icon" title="View">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                  </router-link>
                  <button
                    type="button"
                    class="btn-icon"
                    title="Remove from top active"
                    @click="removeFromTopActive(org)"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M18 6 6 18"/>
                      <path d="m6 6 12 12"/>
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-else class="top-active-empty">Drag an organization here to mark it as top active</p>
        </div>
      </section>
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

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { organizationsApi } from '@/services/api'
import { renderMarkdownForNotes, sanitizeOrgNameForPath } from '@/utils/markdownNotes'
import Modal from '@/components/common/Modal.vue'

const router = useRouter()

const organizations = ref([])
const totalCount = ref(0)
const currentSkip = ref(0)
const limit = 50
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')

const VIEW_MODE_KEY = 'organizations-view-mode'
const viewMode = ref(
  (typeof localStorage !== 'undefined' && localStorage.getItem(VIEW_MODE_KEY)) === 'table' ? 'table' : 'tiles'
)
function setViewMode(mode) {
  viewMode.value = mode
  try { localStorage.setItem(VIEW_MODE_KEY, mode) } catch (_) {}
}

// Section viewer modal state
const showSectionViewer = ref(false)
const viewingOrganization = ref(null)
const viewingSection = ref('')

const hasMore = computed(() => {
  return organizations.value.length < totalCount.value
})

const filteredOrganizations = computed(() => {
  const list = !searchQuery.value.trim()
    ? organizations.value
    : organizations.value.filter(org =>
        (org.name || '').toLowerCase().includes(searchQuery.value.toLowerCase().trim())
      )
  return [...list].sort((a, b) =>
    (a.name || '').localeCompare(b.name || '', undefined, { sensitivity: 'base' })
  )
})

function isTopActive(org) {
  return org && (org.is_top_active === true || org.is_top_active === 1)
}
const topActiveOrganizations = computed(() =>
  organizations.value.filter(o => isTopActive(o))
    .sort((a, b) => (a.name || '').localeCompare(b.name || '', undefined, { sensitivity: 'base' }))
)

const topActiveDragOver = ref(false)

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

const notesImagesContextBase = computed(() =>
  viewingOrganization.value?.name ? sanitizeOrgNameForPath(viewingOrganization.value.name) : ''
)
const renderedSectionContent = computed(() => {
  if (!viewingOrganization.value || !viewingSection.value) return ''
  const content = viewingOrganization.value[viewingSection.value] || ''
  return renderMarkdownForNotes(content, notesImagesContextBase.value)
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

function getSectionsSummary(organization) {
  const parts = []
  if (organization.stakeholders) parts.push('Stakeholders')
  if (organization.team) parts.push('Team')
  if (organization.description) parts.push('Strategy')
  if (organization.related_products) parts.push('Products')
  return parts.length ? parts.join(', ') : '—'
}

function goToEdit(organization) {
  router.push({ name: 'OrganizationEdit', params: { id: organization.id } })
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
    router.push({ name: 'OrganizationEdit', params: { id: org.id } })
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

function onOrgDragStart(event, organization) {
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('application/json', JSON.stringify({ organizationId: organization.id }))
}

async function onTopActiveDrop(event) {
  topActiveDragOver.value = false
  let data
  try {
    const raw = event.dataTransfer.getData('application/json')
    data = raw ? JSON.parse(raw) : null
  } catch {
    return
  }
  const id = data?.organizationId
  if (!id) return
  const org = organizations.value.find(o => o.id === id)
  if (!org || isTopActive(org)) return
  try {
    const response = await organizationsApi.update(id, { is_top_active: true })
    const idx = organizations.value.findIndex(o => o.id === id)
    if (idx !== -1) {
      organizations.value = [
        ...organizations.value.slice(0, idx),
        { ...organizations.value[idx], ...response.data },
        ...organizations.value.slice(idx + 1)
      ]
    }
  } catch (err) {
    console.error('Failed to set top active:', err)
    alert(err.response?.data?.detail || 'Failed to update organization')
  }
}

async function removeFromTopActive(org) {
  try {
    const response = await organizationsApi.update(org.id, { is_top_active: false })
    const idx = organizations.value.findIndex(o => o.id === org.id)
    if (idx !== -1) {
      organizations.value = [
        ...organizations.value.slice(0, idx),
        { ...organizations.value[idx], ...response.data },
        ...organizations.value.slice(idx + 1)
      ]
    }
  } catch (err) {
    console.error('Failed to remove from top active:', err)
    alert(err.response?.data?.detail || 'Failed to update organization')
  }
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

.search-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.search-input-wrapper {
  position: relative;
  flex: 1;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 0.625rem 2.25rem 0.625rem 2.5rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.9375rem;
  background: white;
  transition: border-color 0.15s, box-shadow 0.15s;
}

:global(.dark) .search-input {
  background: #1e293b;
  border-color: #334155;
  color: #f1f5f9;
}

.search-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.search-input::placeholder {
  color: #9ca3af;
}

.clear-search {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  padding: 0.25rem;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-search:hover {
  background: #f3f4f6;
  color: #6b7280;
}

:global(.dark) .clear-search:hover {
  background: #334155;
  color: #f1f5f9;
}

.search-results-count {
  font-size: 0.8125rem;
  color: #6b7280;
  white-space: nowrap;
}

.view-toggle {
  display: flex;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  overflow: hidden;
  background: white;
}

:global(.dark) .view-toggle {
  border-color: #334155;
  background: #1e293b;
}

.toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.toggle-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

:global(.dark) .toggle-btn:hover {
  background: #334155;
  color: #f1f5f9;
}

.toggle-btn.active {
  background: #e0e7ff;
  color: #3730a3;
}

:global(.dark) .toggle-btn.active {
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

.table-container {
  overflow-x: auto;
  background: white;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
}

:global(.dark) .table-container {
  background: #1e293b;
  border-color: #334155;
}

.organizations-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9375rem;
}

.organizations-table th,
.organizations-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

:global(.dark) .organizations-table th,
:global(.dark) .organizations-table td {
  border-bottom-color: #334155;
}

.organizations-table th {
  font-weight: 600;
  color: #374151;
  background: #f9fafb;
}

:global(.dark) .organizations-table th {
  color: #94a3b8;
  background: #0f172a;
}

.organizations-table tbody tr:hover {
  background: #f9fafb;
}

:global(.dark) .organizations-table tbody tr:hover {
  background: #334155;
}

.col-name {
  min-width: 180px;
}

.col-created {
  white-space: nowrap;
  color: #6b7280;
}

:global(.dark) .col-created {
  color: #94a3b8;
}

.col-sections {
  max-width: 220px;
  font-size: 0.8125rem;
  color: #6b7280;
}

:global(.dark) .col-sections {
  color: #94a3b8;
}

.col-actions {
  white-space: nowrap;
}

.col-actions .btn-icon {
  margin-right: 0.125rem;
}

.table-org-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.table-avatar {
  width: 28px;
  height: 28px;
  font-size: 0.6875rem;
}

.org-name-link {
  font-weight: 600;
  color: #111827;
  text-decoration: none;
}

.org-name-link:hover {
  text-decoration: underline;
  color: #2563eb;
}

:global(.dark) .org-name-link {
  color: #f1f5f9;
}

:global(.dark) .org-name-link:hover {
  color: #60a5fa;
}

.sections-summary {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  display: flex;
  gap: 0.5rem;
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

.top-active-section {
  margin-top: 2.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

:global(.dark) .top-active-section {
  border-top-color: #334155;
}

.top-active-heading {
  margin: 0 0 0.75rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
}

:global(.dark) .top-active-heading {
  color: #f1f5f9;
}

.top-active-drop-zone {
  min-height: 80px;
  padding: 1rem;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  background: #f9fafb;
  transition: background 0.15s, border-color 0.15s;
}

:global(.dark) .top-active-drop-zone {
  border-color: #334155;
  background: #0f172a;
}

.top-active-drop-zone.drag-over {
  background: #eff6ff;
  border-color: #2563eb;
}

:global(.dark) .top-active-drop-zone.drag-over {
  background: rgba(59, 130, 246, 0.15);
  border-color: #3b82f6;
}

.top-active-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.top-active-table th,
.top-active-table td {
  padding: 0.5rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

:global(.dark) .top-active-table th,
:global(.dark) .top-active-table td {
  border-bottom-color: #334155;
}

.top-active-table .col-actions {
  width: 100px;
}

.top-active-empty {
  margin: 0;
  color: #6b7280;
  font-size: 0.875rem;
}

:global(.dark) .top-active-empty {
  color: #94a3b8;
}

.organization-card[draggable="true"] {
  cursor: grab;
}

.organization-card[draggable="true"]:active {
  cursor: grabbing;
}

.org-row[draggable="true"] {
  cursor: grab;
}

.org-row[draggable="true"]:active {
  cursor: grabbing;
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

.markdown-preview :deep(ul) {
  list-style-type: disc;
  list-style-position: outside;
  padding-left: 1.25rem;
  margin: 0 0 0.75rem 0;
}

.markdown-preview :deep(ol) {
  list-style-type: decimal;
  list-style-position: outside;
  padding-left: 1.25rem;
  margin: 0 0 0.75rem 0;
}

.markdown-preview :deep(li) {
  display: list-item;
  margin: 0.125rem 0;
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

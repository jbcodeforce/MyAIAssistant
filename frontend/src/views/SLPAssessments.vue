<template>
  <div class="slp-view">
    <div class="view-header">
      <div>
        <h2>Strategic Life Portfolio</h2>
        <p class="view-description">
          Assess and visualize how you allocate time across life dimensions
        </p>
      </div>
      <div class="header-actions">
        <button class="btn-primary" @click="openCreateModal">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 5v14"/>
            <path d="M5 12h14"/>
          </svg>
          New Assessment
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading assessments...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadAssessments" class="btn-primary">Retry</button>
    </div>

    <div v-else class="slp-content">
      <!-- Assessments Table -->
      <div class="table-section">
        <h3 class="section-title">Assessment History</h3>
        
        <div v-if="store.assessments.length === 0" class="empty-state">
          <div class="empty-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2"/>
            </svg>
          </div>
          <p>No assessments yet</p>
          <p class="empty-hint">Create your first life portfolio assessment to start tracking</p>
        </div>

        <div v-else class="table-container">
          <table class="assessments-table">
            <thead>
              <tr>
                <th class="col-date">Date</th>
                <th class="col-summary">Balance Summary</th>
                <th class="col-actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="assessment in store.assessments" 
                :key="assessment.id"
                :class="{ selected: selectedAssessmentId === assessment.id }"
                @click="selectAssessment(assessment.id)"
              >
                <td class="col-date">
                  <span class="date-main">{{ formatDate(assessment.created_at) }}</span>
                  <span class="date-time">{{ formatTime(assessment.created_at) }}</span>
                </td>
                <td class="col-summary">
                  <div class="balance-indicators">
                    <span class="indicator aligned" :title="`${getAlignedCount(assessment)} aligned`">
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                      </svg>
                      {{ getAlignedCount(assessment) }}
                    </span>
                    <span class="indicator neglected" :title="`${getNeglectedCount(assessment)} neglected`">
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" x2="12" y1="8" y2="12"/>
                        <line x1="12" x2="12.01" y1="16" y2="16"/>
                      </svg>
                      {{ getNeglectedCount(assessment) }}
                    </span>
                    <span class="indicator overinvested" :title="`${getOverinvestedCount(assessment)} over-invested`">
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                        <line x1="12" x2="12" y1="9" y2="13"/>
                        <line x1="12" x2="12.01" y1="17" y2="17"/>
                      </svg>
                      {{ getOverinvestedCount(assessment) }}
                    </span>
                  </div>
                </td>
                <td class="col-actions">
                  <button class="btn-icon" @click.stop="openEditModal(assessment)" title="Edit">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                      <path d="m15 5 4 4"/>
                    </svg>
                  </button>
                  <button class="btn-icon danger" @click.stop="handleDelete(assessment)" title="Delete">
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
      </div>

      <!-- Bubble Matrix Chart -->
      <div class="matrix-section" v-if="selectedAssessment">
        <h3 class="section-title">
          Life Balance Matrix
          <span class="section-subtitle">{{ formatDate(selectedAssessment.created_at) }}</span>
        </h3>
        <div class="matrix-container">
          <BubbleMatrix :data="bubbleData" />
        </div>
        <div class="matrix-legend">
          <div class="legend-row">
            <div class="legend-item">
              <span class="legend-dot aligned"></span>
              <span>Aligned (high importance, high time)</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot neglected"></span>
              <span>Neglected (high importance, low time)</span>
            </div>
          </div>
          <div class="legend-row">
            <div class="legend-item">
              <span class="legend-dot overinvested"></span>
              <span>Over-invested (low importance, high time)</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot optimal"></span>
              <span>Optimal low (low importance, low time)</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <Modal :show="showModal" :title="isEditing ? 'Edit Assessment' : 'New Assessment'" @close="closeModal" size="large">
      <form @submit.prevent="handleSubmit" class="assessment-form">
        <div class="form-intro">
          <p>Rate each life dimension from 0-10 for both importance and time spent.</p>
        </div>
        
        <div class="dimensions-grid">
          <div 
            v-for="dim in LIFE_DIMENSIONS" 
            :key="dim.key" 
            class="dimension-card"
            :class="getCategoryClass(dim.category)"
          >
            <div class="dimension-header">
              <span class="dimension-label">{{ dim.label }}</span>
              <span class="dimension-category">{{ dim.category }}</span>
            </div>
            <div class="dimension-inputs">
              <div class="input-group">
                <label :for="`${dim.key}-importance`">Importance</label>
                <input 
                  :id="`${dim.key}-importance`"
                  type="range"
                  min="0"
                  max="10"
                  v-model.number="formData[dim.key].importance"
                />
                <span class="input-value">{{ formData[dim.key].importance }}</span>
              </div>
              <div class="input-group">
                <label :for="`${dim.key}-time`">Time Spent</label>
                <input 
                  :id="`${dim.key}-time`"
                  type="range"
                  min="0"
                  max="10"
                  v-model.number="formData[dim.key].time_spent"
                />
                <span class="input-value">{{ formData[dim.key].time_spent }}</span>
              </div>
            </div>
          </div>
        </div>
      </form>

      <template #footer>
        <button type="button" class="btn-secondary" @click="closeModal">Cancel</button>
        <button type="button" class="btn-primary" @click="handleSubmit" :disabled="submitting">
          {{ submitting ? 'Saving...' : (isEditing ? 'Update' : 'Create') }}
        </button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { useSlpAssessmentStore, LIFE_DIMENSIONS } from '@/stores/slpAssessmentStore'
import Modal from '@/components/common/Modal.vue'
import BubbleMatrix from '@/components/metrics/BubbleMatrix.vue'

const store = useSlpAssessmentStore()

const loading = computed(() => store.loading)
const error = computed(() => store.error)

// Modal state
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const selectedAssessmentId = ref(null)

// Form data initialized with all dimensions
const createEmptyFormData = () => {
  const data = {}
  LIFE_DIMENSIONS.forEach(dim => {
    data[dim.key] = { importance: 5, time_spent: 5 }
  })
  return data
}

const formData = reactive(createEmptyFormData())

// Selected assessment for matrix display
const selectedAssessment = computed(() => {
  if (selectedAssessmentId.value) {
    return store.assessments.find(a => a.id === selectedAssessmentId.value)
  }
  return store.latestAssessment
})

// Bubble data for matrix
const bubbleData = computed(() => {
  return store.assessmentToBubbleData(selectedAssessment.value)
})

// Watch for assessments to auto-select the latest
watch(() => store.assessments, (newAssessments) => {
  if (newAssessments.length > 0 && !selectedAssessmentId.value) {
    selectedAssessmentId.value = newAssessments[0].id
  }
}, { immediate: true })

onMounted(() => {
  loadAssessments()
})

async function loadAssessments() {
  try {
    await store.fetchAssessments({ limit: 50 })
  } catch (err) {
    console.error('Failed to load assessments:', err)
  }
}

function selectAssessment(id) {
  selectedAssessmentId.value = id
}

// Balance calculation helpers
function getQuadrantCounts(assessment) {
  let aligned = 0
  let neglected = 0
  let overinvested = 0
  let optimal = 0
  
  LIFE_DIMENSIONS.forEach(dim => {
    const importance = assessment[dim.key]?.importance || 0
    const timeSpent = assessment[dim.key]?.time_spent || 0
    
    if (importance >= 5 && timeSpent >= 5) aligned++
    else if (importance >= 5 && timeSpent < 5) neglected++
    else if (importance < 5 && timeSpent >= 5) overinvested++
    else optimal++
  })
  
  return { aligned, neglected, overinvested, optimal }
}

function getAlignedCount(assessment) {
  return getQuadrantCounts(assessment).aligned
}

function getNeglectedCount(assessment) {
  return getQuadrantCounts(assessment).neglected
}

function getOverinvestedCount(assessment) {
  return getQuadrantCounts(assessment).overinvested
}

function getCategoryClass(category) {
  return `category-${category.toLowerCase()}`
}

function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

function formatTime(dateString) {
  const date = new Date(dateString)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

function openCreateModal() {
  isEditing.value = false
  editingId.value = null
  Object.assign(formData, createEmptyFormData())
  showModal.value = true
}

function openEditModal(assessment) {
  isEditing.value = true
  editingId.value = assessment.id
  
  // Populate form with assessment data
  LIFE_DIMENSIONS.forEach(dim => {
    formData[dim.key] = {
      importance: assessment[dim.key]?.importance || 5,
      time_spent: assessment[dim.key]?.time_spent || 5
    }
  })
  
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  isEditing.value = false
  editingId.value = null
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (isEditing.value) {
      await store.updateAssessment(editingId.value, { ...formData })
    } else {
      const created = await store.createAssessment({ ...formData })
      selectedAssessmentId.value = created.id
    }
    closeModal()
  } catch (err) {
    console.error('Failed to save assessment:', err)
  } finally {
    submitting.value = false
  }
}

async function handleDelete(assessment) {
  if (!confirm(`Delete assessment from ${formatDate(assessment.created_at)}?`)) {
    return
  }
  
  try {
    await store.deleteAssessment(assessment.id)
    if (selectedAssessmentId.value === assessment.id) {
      selectedAssessmentId.value = store.assessments[0]?.id || null
    }
  } catch (err) {
    console.error('Failed to delete assessment:', err)
  }
}
</script>

<style scoped>
.slp-view {
  min-height: calc(100vh - 52px);
  background: linear-gradient(135deg, #faf5ff 0%, #f0f9ff 50%, #f0fdf4 100%);
  padding: 2rem;
  width: 100%;
}

:global(.dark) .slp-view {
  background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 50%, #052e16 100%);
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.view-header h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.875rem;
  font-weight: 700;
  color: #1e1b4b;
  font-family: 'Crimson Pro', Georgia, serif;
}

:global(.dark) .view-header h2 {
  color: #e0e7ff;
}

.view-description {
  margin: 0;
  color: #6366f1;
  font-size: 1rem;
}

:global(.dark) .view-description {
  color: #a5b4fc;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9375rem;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: white;
  color: #4b5563;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #f9fafb;
  border-color: #9ca3af;
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

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p,
.error-state p {
  font-size: 1.125rem;
  color: #6b7280;
}

.slp-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Table Section */
.table-section {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.1);
}

:global(.dark) .table-section {
  background: rgba(30, 27, 75, 0.6);
  border-color: rgba(99, 102, 241, 0.2);
}

.section-title {
  margin: 0 0 1.25rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #1e1b4b;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

:global(.dark) .section-title {
  color: #e0e7ff;
}

.section-subtitle {
  font-size: 0.875rem;
  font-weight: 400;
  color: #6366f1;
}

.empty-state {
  text-align: center;
  padding: 3rem 2rem;
}

.empty-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
  color: #a5b4fc;
}

.empty-state p {
  margin: 0;
  color: #6366f1;
  font-size: 1.125rem;
}

.empty-hint {
  margin-top: 0.5rem !important;
  font-size: 0.875rem !important;
  color: #94a3b8 !important;
}

.table-container {
  overflow-x: auto;
}

.assessments-table {
  width: 100%;
  border-collapse: collapse;
}

.assessments-table th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6366f1;
  border-bottom: 2px solid #e0e7ff;
}

:global(.dark) .assessments-table th {
  color: #a5b4fc;
  border-bottom-color: rgba(99, 102, 241, 0.3);
}

.assessments-table td {
  padding: 0.875rem 1rem;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

:global(.dark) .assessments-table td {
  border-bottom-color: rgba(99, 102, 241, 0.1);
}

.assessments-table tbody tr {
  cursor: pointer;
  transition: all 0.15s;
}

.assessments-table tbody tr:hover {
  background: rgba(99, 102, 241, 0.05);
}

.assessments-table tbody tr.selected {
  background: rgba(99, 102, 241, 0.1);
}

:global(.dark) .assessments-table tbody tr.selected {
  background: rgba(99, 102, 241, 0.2);
}

.col-date {
  width: 160px;
}

.date-main {
  display: block;
  font-weight: 500;
  color: #1e1b4b;
}

:global(.dark) .date-main {
  color: #e0e7ff;
}

.date-time {
  display: block;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.125rem;
}

.col-summary {
  min-width: 200px;
}

.balance-indicators {
  display: flex;
  gap: 1rem;
}

.indicator {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.625rem;
  border-radius: 20px;
  font-size: 0.8125rem;
  font-weight: 600;
}

.indicator.aligned {
  background: #dcfce7;
  color: #166534;
}

.indicator.neglected {
  background: #fef3c7;
  color: #92400e;
}

.indicator.overinvested {
  background: #fee2e2;
  color: #991b1b;
}

:global(.dark) .indicator.aligned {
  background: rgba(34, 197, 94, 0.2);
  color: #86efac;
}

:global(.dark) .indicator.neglected {
  background: rgba(234, 179, 8, 0.2);
  color: #fde047;
}

:global(.dark) .indicator.overinvested {
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
}

.col-actions {
  width: 100px;
  text-align: center;
}

.btn-icon {
  padding: 0.5rem;
  border: none;
  background: transparent;
  color: #6b7280;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-icon:hover {
  background: #f3f4f6;
  color: #6366f1;
}

.btn-icon.danger:hover {
  background: #fee2e2;
  color: #dc2626;
}

:global(.dark) .btn-icon:hover {
  background: rgba(99, 102, 241, 0.2);
}

:global(.dark) .btn-icon.danger:hover {
  background: rgba(239, 68, 68, 0.2);
}

/* Matrix Section */
.matrix-section {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.1);
}

:global(.dark) .matrix-section {
  background: rgba(30, 27, 75, 0.6);
  border-color: rgba(99, 102, 241, 0.2);
}

.matrix-container {
  margin: 1.5rem 0;
}

.matrix-legend {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e7ff;
}

:global(.dark) .matrix-legend {
  border-top-color: rgba(99, 102, 241, 0.2);
}

.legend-row {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
  color: #4b5563;
}

:global(.dark) .legend-item {
  color: #a5b4fc;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-dot.aligned {
  background: #22c55e;
}

.legend-dot.neglected {
  background: #f59e0b;
}

.legend-dot.overinvested {
  background: #ef4444;
}

.legend-dot.optimal {
  background: #6366f1;
}

/* Form Styles */
.assessment-form {
  padding: 0.5rem 0;
}

.form-intro {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f0f9ff;
  border-radius: 10px;
  border-left: 4px solid #6366f1;
}

.form-intro p {
  margin: 0;
  font-size: 0.9375rem;
  color: #1e40af;
}

.dimensions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.dimension-card {
  background: #fafafa;
  border-radius: 12px;
  padding: 1rem;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.dimension-card:hover {
  border-color: #a5b4fc;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
}

.dimension-card.category-relationships {
  border-left: 4px solid #ec4899;
}

.dimension-card.category-health {
  border-left: 4px solid #22c55e;
}

.dimension-card.category-personal {
  border-left: 4px solid #a855f7;
}

.dimension-card.category-social {
  border-left: 4px solid #3b82f6;
}

.dimension-card.category-career {
  border-left: 4px solid #f97316;
}

.dimension-card.category-growth {
  border-left: 4px solid #14b8a6;
}

.dimension-card.category-resources {
  border-left: 4px solid #eab308;
}

.dimension-card.category-leisure {
  border-left: 4px solid #8b5cf6;
}

.dimension-card.category-basic {
  border-left: 4px solid #64748b;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.dimension-label {
  font-weight: 600;
  font-size: 0.9375rem;
  color: #1e1b4b;
}

.dimension-category {
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6b7280;
  background: #e5e7eb;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
}

.dimension-inputs {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.input-group label {
  font-size: 0.75rem;
  color: #6b7280;
  width: 75px;
  flex-shrink: 0;
}

.input-group input[type="range"] {
  flex: 1;
  height: 6px;
  appearance: none;
  background: #e5e7eb;
  border-radius: 3px;
  cursor: pointer;
}

.input-group input[type="range"]::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  background: #6366f1;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.15s;
}

.input-group input[type="range"]::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

.input-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6366f1;
  width: 20px;
  text-align: right;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}

@media (max-width: 768px) {
  .slp-view {
    padding: 1rem;
  }

  .view-header {
    flex-direction: column;
    gap: 1rem;
  }

  .balance-indicators {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .legend-row {
    flex-direction: column;
    gap: 0.5rem;
  }

  .dimensions-grid {
    grid-template-columns: 1fr;
  }
}
</style>


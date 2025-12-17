<template>
  <div class="customers-view">
    <div class="view-header">
      <div>
        <h2>Customers</h2>
        <p class="view-description">
          Manage customer profiles, stakeholders, and strategy information
        </p>
      </div>
      <div class="header-actions">
        <span class="customer-count" v-if="!loading && !error">
          {{ totalCount }} customer{{ totalCount !== 1 ? 's' : '' }}
        </span>
        <button class="btn-primary" @click="openCreateModal">
          + New Customer
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading customers...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadCustomers" class="btn-primary">Retry</button>
    </div>

    <div v-else class="customers-content">
      <div v-if="customers.length === 0" class="empty-state">
        <p>No customers found</p>
        <p class="empty-state-hint">
          Add customers to track stakeholders and strategy information
        </p>
      </div>

      <div v-else class="customers-grid">
        <div 
          v-for="customer in customers" 
          :key="customer.id" 
          class="customer-card"
        >
          <div class="customer-header">
            <div class="customer-avatar">
              {{ getInitials(customer.name) }}
            </div>
            <div class="customer-actions">
              <button class="btn-icon" @click="openEditModal(customer)" title="Edit">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                  <path d="m15 5 4 4"/>
                </svg>
              </button>
              <button class="btn-icon danger" @click="handleDelete(customer)" title="Delete">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 6h18"/>
                  <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                  <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                </svg>
              </button>
            </div>
          </div>

          <h3 class="customer-name">{{ customer.name }}</h3>

          <div class="customer-details">
            <div class="detail-section" v-if="customer.stakeholders">
              <h4>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
                Stakeholders
              </h4>
              <p>{{ truncate(customer.stakeholders, 80) }}</p>
            </div>

            <div class="detail-section" v-if="customer.team">
              <h4>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
                Team
              </h4>
              <p>{{ truncate(customer.team, 80) }}</p>
            </div>

            <div class="detail-section" v-if="customer.description">
              <h4>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
                Strategy
              </h4>
              <p>{{ truncate(customer.description, 120) }}</p>
            </div>

            <div class="detail-section" v-if="customer.related_products">
              <h4>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="m7.5 4.27 9 5.15"/>
                  <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>
                  <path d="m3.3 7 8.7 5 8.7-5"/>
                  <path d="M12 22V12"/>
                </svg>
                Products
              </h4>
              <p>{{ truncate(customer.related_products, 80) }}</p>
            </div>
          </div>

          <div class="customer-meta">
            <span class="meta-item">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>
                <line x1="16" x2="16" y1="2" y2="6"/>
                <line x1="8" x2="8" y1="2" y2="6"/>
                <line x1="3" x2="21" y1="10" y2="10"/>
              </svg>
              Added {{ formatDate(customer.created_at) }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="hasMore" class="load-more">
        <button @click="loadMore" class="btn-secondary">
          Load More ({{ customers.length }} of {{ totalCount }})
        </button>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <Modal :show="showModal" :title="isEditing ? 'Edit Customer' : 'New Customer'" @close="closeModal">
      <form @submit.prevent="handleSubmit" class="customer-form">
        <div class="form-group">
          <label for="name">Customer Name *</label>
          <input 
            id="name" 
            v-model="formData.name" 
            type="text" 
            required 
            placeholder="Enter customer or company name"
          />
        </div>

        <div class="form-group">
          <label for="stakeholders">Stakeholders</label>
          <textarea 
            id="stakeholders" 
            v-model="formData.stakeholders" 
            rows="2"
            placeholder="Key contacts: John Doe (CTO), Jane Smith (PM)"
          ></textarea>
          <span class="form-hint">Key decision makers and contacts</span>
        </div>

        <div class="form-group">
          <label for="team">Team</label>
          <textarea 
            id="team" 
            v-model="formData.team" 
            rows="2"
            placeholder="Internal team members working with this customer"
          ></textarea>
          <span class="form-hint">Your team members assigned to this customer</span>
        </div>

        <div class="form-group">
          <label for="description">Strategy / Notes</label>
          <textarea 
            id="description" 
            v-model="formData.description" 
            rows="4"
            placeholder="Customer strategy, goals, and important notes"
          ></textarea>
          <span class="form-hint">Overall strategy and relationship notes</span>
        </div>

        <div class="form-group">
          <label for="related_products">Related Products</label>
          <textarea 
            id="related_products" 
            v-model="formData.related_products" 
            rows="2"
            placeholder="Products or services used by this customer"
          ></textarea>
          <span class="form-hint">Products, services, or solutions relevant to this customer</span>
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
import { customersApi } from '@/services/api'
import Modal from '@/components/common/Modal.vue'

const customers = ref([])
const totalCount = ref(0)
const currentSkip = ref(0)
const limit = 50
const loading = ref(false)
const error = ref(null)

// Modal state
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const formData = ref({
  name: '',
  stakeholders: '',
  team: '',
  description: '',
  related_products: ''
})

const hasMore = computed(() => {
  return customers.value.length < totalCount.value
})

const isFormValid = computed(() => {
  return formData.value.name && formData.value.name.trim().length > 0
})

onMounted(async () => {
  await loadCustomers()
})

async function loadCustomers() {
  loading.value = true
  error.value = null
  try {
    const response = await customersApi.list({ skip: 0, limit })
    customers.value = response.data.customers
    totalCount.value = response.data.total
    currentSkip.value = response.data.customers.length
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load customers'
    console.error('Failed to load customers:', err)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  try {
    const response = await customersApi.list({ skip: currentSkip.value, limit })
    customers.value = [...customers.value, ...response.data.customers]
    currentSkip.value = customers.value.length
  } catch (err) {
    console.error('Failed to load more customers:', err)
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

function openCreateModal() {
  isEditing.value = false
  editingId.value = null
  formData.value = {
    name: '',
    stakeholders: '',
    team: '',
    description: '',
    related_products: ''
  }
  showModal.value = true
}

function openEditModal(customer) {
  isEditing.value = true
  editingId.value = customer.id
  formData.value = {
    name: customer.name,
    stakeholders: customer.stakeholders || '',
    team: customer.team || '',
    description: customer.description || '',
    related_products: customer.related_products || ''
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
      const response = await customersApi.update(editingId.value, formData.value)
      const index = customers.value.findIndex(c => c.id === editingId.value)
      if (index !== -1) {
        customers.value[index] = response.data
      }
    } else {
      const response = await customersApi.create(formData.value)
      customers.value.unshift(response.data)
      totalCount.value++
    }
    closeModal()
  } catch (err) {
    console.error('Failed to save customer:', err)
    alert(err.response?.data?.detail || 'Failed to save customer')
  }
}

async function handleDelete(customer) {
  if (confirm(`Delete customer "${customer.name}"? This will not delete associated projects.`)) {
    try {
      await customersApi.delete(customer.id)
      customers.value = customers.value.filter(c => c.id !== customer.id)
      totalCount.value--
    } catch (err) {
      console.error('Failed to delete customer:', err)
      alert(err.response?.data?.detail || 'Failed to delete customer')
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
.customers-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .customers-view {
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

.customer-count {
  padding: 0.375rem 0.75rem;
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

:global(.dark) .customer-count {
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

.customers-content {
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

.customers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 1.25rem;
}

.customer-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 1.5rem;
  transition: all 0.2s;
}

:global(.dark) .customer-card {
  background: #1e293b;
  border-color: #334155;
}

.customer-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.customer-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.customer-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  letter-spacing: -0.025em;
}

.customer-actions {
  display: flex;
  gap: 0.25rem;
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

:global(.dark) .btn-icon:hover {
  background: #334155;
  color: #f1f5f9;
}

.btn-icon.danger:hover {
  background: #fee2e2;
  color: #dc2626;
}

.customer-name {
  margin: 0 0 1rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
}

:global(.dark) .customer-name {
  color: #f1f5f9;
}

.customer-details {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
  margin-bottom: 1rem;
}

.detail-section h4 {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  margin: 0 0 0.25rem 0;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6b7280;
}

.detail-section h4 svg {
  color: #9ca3af;
}

.detail-section p {
  margin: 0;
  font-size: 0.8125rem;
  color: #374151;
  line-height: 1.5;
}

:global(.dark) .detail-section p {
  color: #94a3b8;
}

.customer-meta {
  display: flex;
  gap: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid #f3f4f6;
}

:global(.dark) .customer-meta {
  border-top-color: #334155;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  color: #9ca3af;
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

/* Form styles */
.customer-form {
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

.form-group input,
.form-group textarea,
.form-group select {
  padding: 0.625rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9375rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}

:global(.dark) .form-group input,
:global(.dark) .form-group textarea,
:global(.dark) .form-group select {
  background: #1e293b;
  border-color: #334155;
  color: #f1f5f9;
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
  min-height: 60px;
}

.form-hint {
  font-size: 0.75rem;
  color: #6b7280;
}

@media (max-width: 768px) {
  .customers-view {
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

  .customers-grid {
    grid-template-columns: 1fr;
  }
}
</style>



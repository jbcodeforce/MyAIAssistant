<template>
  <div class="agents-view">
    <div class="view-header">
      <div>
        <h2>Agents</h2>
        <p class="view-description">
          View configured agents
        </p>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading agents...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadAgents" class="btn-primary">Retry</button>
    </div>

    <div v-else class="agents-content">
      <div v-if="agents.length === 0" class="empty-state">
        <p>No agents found</p>
        <p class="empty-state-hint">
          Agents are loaded from the agent config directory
        </p>
      </div>

      <div v-else class="agents-grid">
        <div
          v-for="agent in agents"
          :key="agent.name"
          class="agent-tile"
          @click="openDetailModal(agent)"
        >
          <h3 class="agent-name">{{ agent.name }}</h3>
          <p class="agent-description">{{ agent.description || 'No description' }}</p>
        </div>
      </div>
    </div>

    <Modal
      :show="showDetailModal"
      :title="selectedAgent ? selectedAgent.name : ''"
      @close="closeDetailModal"
    >
      <div v-if="selectedAgent" class="agent-detail">
        <p class="agent-detail-description">{{ selectedAgent.description || 'No description' }}</p>
        <dl class="agent-detail-params">
          <dt>Model</dt>
          <dd>{{ selectedAgent.model ?? '—' }}</dd>
          <dt>Temperature</dt>
          <dd>{{ selectedAgent.temperature != null ? selectedAgent.temperature : '—' }}</dd>
          <dt>Max tokens</dt>
          <dd>{{ selectedAgent.max_tokens != null ? selectedAgent.max_tokens : '—' }}</dd>
        </dl>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { agentsApi } from '@/services/api'
import Modal from '@/components/common/Modal.vue'

const agents = ref([])
const loading = ref(true)
const error = ref(null)
const showDetailModal = ref(false)
const selectedAgent = ref(null)

async function loadAgents() {
  loading.value = true
  error.value = null
  try {
    const response = await agentsApi.list()
    agents.value = Array.isArray(response.data) ? response.data : []
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Failed to load agents'
  } finally {
    loading.value = false
  }
}

function openDetailModal(agent) {
  selectedAgent.value = agent
  showDetailModal.value = true
}

function closeDetailModal() {
  showDetailModal.value = false
  selectedAgent.value = null
}

onMounted(() => {
  loadAgents()
})
</script>

<style scoped>
.agents-view {
  padding: 1.5rem;
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
  font-weight: 600;
  color: #111827;
}

.view-description {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
}

:global(.dark) .view-header h2 {
  color: #f1f5f9;
}

:global(.dark) .view-description {
  color: #94a3b8;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 4rem 2rem;
}

.loading-state p,
.error-state p {
  margin: 0;
  font-size: 1.125rem;
  color: #6b7280;
}

:global(.dark) .loading-state p,
:global(.dark) .error-state p {
  color: #94a3b8;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
}

.empty-state p {
  margin: 0;
  font-size: 1.125rem;
  color: #6b7280;
}

.empty-state-hint {
  margin-top: 0.5rem !important;
  font-size: 0.875rem !important;
  color: #9ca3af;
}

:global(.dark) .empty-state {
  background: #1e293b;
  border-color: #334155;
}

:global(.dark) .empty-state p {
  color: #94a3b8;
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}

.agent-tile {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 1.25rem;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
  cursor: pointer;
}

.agent-tile:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

:global(.dark) .agent-tile {
  background: #1e293b;
  border-color: #334155;
}

.agent-name {
  margin: 0 0 0.5rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
}

:global(.dark) .agent-name {
  color: #f1f5f9;
}

.agent-description {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.4;
}

:global(.dark) .agent-description {
  color: #94a3b8;
}

.agent-detail {
  padding: 0.25rem 0;
}

.agent-detail-description {
  margin: 0 0 1.25rem 0;
  font-size: 0.9375rem;
  color: #6b7280;
  line-height: 1.5;
}

:global(.dark) .agent-detail-description {
  color: #94a3b8;
}

.agent-detail-params {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.5rem 1.5rem;
  margin: 0;
}

.agent-detail-params dt {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.agent-detail-params dd {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
}

:global(.dark) .agent-detail-params dt {
  color: #cbd5e1;
}

:global(.dark) .agent-detail-params dd {
  color: #94a3b8;
}

@media (max-width: 640px) {
  .agents-grid {
    grid-template-columns: 1fr;
  }
}
</style>

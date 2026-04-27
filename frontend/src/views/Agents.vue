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
          Set agent_service_url in backend config and ensure the agent service is running (GET /myai/agents)
        </p>
      </div>

      <div v-else class="agents-grid">
        <div
          v-for="agent in agents"
          :key="agent.agent_name"
          class="agent-tile"
        >
          <div class="agent-tile-header">
            <h3 class="agent-name">{{ agent.agent_name }}</h3>
            <span v-if="agent.default" class="agent-badge">default</span>
          </div>
          <p class="agent-description">{{ agent.description || 'No description' }}</p>
          <div class="agent-tile-actions">
            <button type="button" class="btn-primary" @click="openChat(agent)">
              Chat
            </button>
            <button type="button" class="btn-secondary" @click="openConfig(agent)">
              Configure
            </button>
          </div>
        </div>
      </div>
    </div>

    <Modal
      :show="showConfigModal"
      :title="configModalTitle"
      @close="closeConfigModal"
    >
      <div v-if="selectedAgent" class="config-detail">
        <p class="config-path-label">Config path</p>
        <p class="config-path">{{ selectedAgent.path_to_config }}</p>
        <button type="button" class="btn-secondary" @click="copyConfigPath">Copy path</button>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { agentsApi } from '@/services/api'
import Modal from '@/components/common/Modal.vue'

const router = useRouter()
const agents = ref([])
const loading = ref(true)
const error = ref(null)
const showConfigModal = ref(false)
const selectedAgent = ref(null)

const configModalTitle = computed(() =>
  selectedAgent.value ? `Configure: ${selectedAgent.value.agent_name}` : 'Configure'
)

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

function openChat(agent) {
  const query = { agent: agent.agent_name }
  if (agent.url) query.agent_url = agent.url
  router.push({ path: '/assistant', query })
}

function openConfig(agent) {
  selectedAgent.value = agent
  showConfigModal.value = true
}

function closeConfigModal() {
  showConfigModal.value = false
  selectedAgent.value = null
}

async function copyConfigPath() {
  if (!selectedAgent.value?.path_to_config) return
  const path = String(selectedAgent.value.path_to_config)
  try {
    await navigator.clipboard.writeText(path)
    closeConfigModal()
  } catch (_) {
    // ignore
  }
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
  transition: box-shadow 0.2s ease;
}

.agent-tile:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.agent-tile-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.agent-badge {
  font-size: 0.6875rem;
  font-weight: 500;
  text-transform: uppercase;
  color: #6b7280;
  background: #f3f4f6;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
}

:global(.dark) .agent-badge {
  color: #94a3b8;
  background: #334155;
}

.agent-tile-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
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

.config-detail {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.config-path-label {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

:global(.dark) .config-path-label {
  color: #cbd5e1;
}

.config-path {
  margin: 0;
  font-size: 0.8125rem;
  font-family: ui-monospace, monospace;
  color: #6b7280;
  word-break: break-all;
}

:global(.dark) .config-path {
  color: #94a3b8;
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
  background: #2563eb;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background: #f9fafb;
}

:global(.dark) .btn-secondary {
  background: #1e293b;
  border-color: #334155;
  color: #e2e8f0;
}

:global(.dark) .btn-secondary:hover {
  background: #334155;
}

@media (max-width: 640px) {
  .agents-grid {
    grid-template-columns: 1fr;
  }
}
</style>

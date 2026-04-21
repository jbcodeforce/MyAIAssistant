<template>
  <div class="assistant-view">
    <div class="view-header">
      <div>
        <h2>Assistant</h2>
        <p class="view-description">
          Chat with your knowledge base, tasks, meetings, and organization
        </p>
      </div>
    </div>
    <div class="assistant-panel-wrapper">
      <AssistantChatPanel :agent-name="agentName" :agent-url="agentUrl" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { agentsApi } from '@/services/api'
import AssistantChatPanel from '@/components/chat/AssistantChatPanel.vue'

const route = useRoute()
const agentName = computed(() => route.query.agent || 'MainAgent')
const agentUrlFromQuery = computed(() => route.query.agent_url || null)
const agentUrlResolved = ref(null)

async function resolveAgentUrl() {
  if (agentUrlFromQuery.value) {
    agentUrlResolved.value = agentUrlFromQuery.value
    return
  }
  const name = agentName.value
  if (!name || name === 'MainAgent') {
    agentUrlResolved.value = null
    return
  }
  try {
    const { data } = await agentsApi.list()
    const agent = Array.isArray(data) ? data.find((a) => a.agent_name === name) : null
    agentUrlResolved.value = agent?.url || null
  } catch {
    agentUrlResolved.value = null
  }
}

const agentUrl = computed(() => agentUrlFromQuery.value || agentUrlResolved.value || null)

onMounted(resolveAgentUrl)
watch([agentName, agentUrlFromQuery], resolveAgentUrl)
</script>

<style scoped>
.assistant-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
  display: flex;
  flex-direction: column;
}

:global(.dark) .assistant-view {
  background: #0f172a;
}

.view-header {
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

:global(.dark) .view-header h2 {
  color: #f1f5f9;
}

:global(.dark) .view-description {
  color: #94a3b8;
}

.assistant-panel-wrapper {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  max-width: 850px;
}

@media (max-width: 768px) {
  .assistant-view {
    padding: 1rem;
  }
}
</style>

<template>
  <div class="meeting-steps-view">
    <div v-if="pastSteps?.length" class="preview-section">
      <h3 class="preview-section-title">Past Steps</h3>
      <div class="steps-list-view">
        <div v-for="(step, index) in pastSteps" :key="'pv-past-' + index" class="step-view-item">
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-content">
            <div class="step-what">{{ step.what }}</div>
            <div class="step-who" v-if="step.who">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              {{ step.who }}
            </div>
            <router-link
              v-if="step.todo_id && taskTodosLink(step.todo_id)"
              :to="taskTodosLink(step.todo_id)"
              class="step-task-link"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              View Task
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <div v-if="nextSteps?.length" class="preview-section">
      <h3 class="preview-section-title">Next Steps</h3>
      <div class="steps-list-view">
        <div v-for="(step, index) in nextSteps" :key="'pv-next-' + index" class="step-view-item">
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-content">
            <div class="step-what">{{ step.what }}</div>
            <div class="step-who" v-if="step.who">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              {{ step.who }}
            </div>
            <button
              v-if="showCreateTask && hasTaskContext && !step.todo_id"
              type="button"
              @click="$emit('create-task', step, index)"
              class="step-create-task-btn"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 5v14"/>
                <path d="M5 12h14"/>
              </svg>
              Create Task
            </button>
            <router-link
              v-else-if="step.todo_id && taskTodosLink(step.todo_id)"
              :to="taskTodosLink(step.todo_id)"
              class="step-task-link"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              View Task
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  pastSteps: {
    type: Array,
    default: () => []
  },
  nextSteps: {
    type: Array,
    default: () => []
  },
  projectId: {
    type: [Number, String],
    default: null
  },
  organizationId: {
    type: [Number, String],
    default: null
  },
  showCreateTask: {
    type: Boolean,
    default: false
  }
})

defineEmits(['create-task'])

const hasTaskContext = computed(() => !!(props.projectId || props.organizationId))

function taskTodosLink(todoId) {
  if (!todoId) return null
  if (props.projectId) {
    return { path: `/projects/${props.projectId}/todos`, query: { highlight: todoId } }
  }
  if (props.organizationId) {
    return { path: `/organizations/${props.organizationId}/todos`, query: { highlight: todoId } }
  }
  return null
}
</script>

<style scoped>
.meeting-steps-view {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.preview-section {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem 1.25rem;
}

:global(.dark) .preview-section {
  background: #1e293b;
  border-color: #334155;
}

.preview-section-title {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

:global(.dark) .preview-section-title {
  color: #94a3b8;
}

.steps-list-view {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.step-view-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.875rem;
  background: #f9fafb;
  border-radius: 8px;
  border-left: 3px solid #3b82f6;
}

:global(.dark) .step-view-item {
  background: #0f172a;
  border-left-color: #60a5fa;
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  background: #3b82f6;
  color: white;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
}

.step-what {
  font-size: 0.9375rem;
  color: #111827;
  line-height: 1.5;
}

:global(.dark) .step-what {
  color: #f1f5f9;
}

.step-who {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  margin-top: 0.375rem;
  font-size: 0.8125rem;
  color: #6b7280;
}

:global(.dark) .step-who {
  color: #94a3b8;
}

.step-who svg {
  opacity: 0.7;
}

.step-task-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  color: #2563eb;
  background: #eff6ff;
  border-radius: 4px;
  text-decoration: none;
  transition: all 0.15s;
}

.step-task-link:hover {
  background: #dbeafe;
  color: #1d4ed8;
}

:global(.dark) .step-task-link {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
}

:global(.dark) .step-task-link:hover {
  background: rgba(59, 130, 246, 0.25);
  color: #93c5fd;
}

.step-create-task-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  color: #16a34a;
  background: #f0fdf4;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.step-create-task-btn:hover {
  background: #dcfce7;
  color: #15803d;
}

:global(.dark) .step-create-task-btn {
  background: rgba(22, 163, 74, 0.15);
  color: #4ade80;
}

:global(.dark) .step-create-task-btn:hover {
  background: rgba(22, 163, 74, 0.25);
  color: #86efac;
}

.step-task-link svg,
.step-create-task-btn svg {
  flex-shrink: 0;
}
</style>

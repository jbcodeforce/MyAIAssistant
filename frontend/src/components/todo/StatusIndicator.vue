<template>
  <span :class="['status-badge', statusClass]">
    {{ status }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true
  }
})

const statusClass = computed(() => {
  const statusMap = {
    'Open': 'status-open',
    'Started': 'status-started',
    'Completed': 'status-completed',
    'Cancelled': 'status-cancelled'
  }
  return statusMap[props.status] || 'status-open'
})
</script>

<style scoped>
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.status-open {
  background-color: #dbeafe;
  color: #1e40af;
}

.status-started {
  background-color: #fef3c7;
  color: #92400e;
}

.status-completed {
  background-color: #d1fae5;
  color: #065f46;
}

.status-cancelled {
  background-color: #f3f4f6;
  color: #6b7280;
}
</style>


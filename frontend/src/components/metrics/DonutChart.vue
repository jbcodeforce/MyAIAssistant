<template>
  <div class="donut-chart">
    <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`">
      <g :transform="`translate(${size/2}, ${size/2})`">
        <!-- Background circle -->
        <circle
          :r="radius"
          fill="none"
          :stroke="bgColor"
          :stroke-width="strokeWidth"
        />
        <!-- Data segments -->
        <circle
          v-for="(segment, index) in segments"
          :key="index"
          :r="radius"
          fill="none"
          :stroke="colors[index % colors.length]"
          :stroke-width="strokeWidth"
          :stroke-dasharray="segment.dashArray"
          :stroke-dashoffset="segment.offset"
          stroke-linecap="round"
          class="segment"
          :style="{ '--delay': index * 0.1 + 's' }"
        />
      </g>
      <!-- Center text -->
      <text
        :x="size / 2"
        :y="size / 2 - 8"
        text-anchor="middle"
        class="total-value"
      >
        {{ total }}
      </text>
      <text
        :x="size / 2"
        :y="size / 2 + 12"
        text-anchor="middle"
        class="total-label"
      >
        Total
      </text>
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    required: true,
    default: () => []
  },
  colors: {
    type: Array,
    default: () => ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444']
  },
  size: {
    type: Number,
    default: 180
  },
  strokeWidth: {
    type: Number,
    default: 24
  }
})

const radius = computed(() => (props.size - props.strokeWidth) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)

const total = computed(() => props.data.reduce((sum, item) => sum + item.value, 0))

const bgColor = computed(() => {
  // Check for dark mode
  if (typeof document !== 'undefined' && document.documentElement.classList.contains('dark')) {
    return '#334155'
  }
  return '#e5e7eb'
})

const segments = computed(() => {
  if (total.value === 0) return []
  
  let cumulativePercent = 0
  const gap = 0.01 // Small gap between segments
  
  return props.data.map((item) => {
    const percent = item.value / total.value
    const adjustedPercent = Math.max(0, percent - gap)
    const dashArray = `${adjustedPercent * circumference.value} ${circumference.value}`
    const offset = -cumulativePercent * circumference.value + circumference.value * 0.25
    
    cumulativePercent += percent
    
    return {
      dashArray,
      offset,
      percent
    }
  })
})
</script>

<style scoped>
.donut-chart {
  display: flex;
  justify-content: center;
  align-items: center;
}

.segment {
  transition: stroke-dasharray 0.8s ease-out, stroke-dashoffset 0.8s ease-out;
  animation: segmentAppear 0.8s ease-out forwards;
  animation-delay: var(--delay);
  opacity: 0;
}

@keyframes segmentAppear {
  from {
    opacity: 0;
    stroke-dasharray: 0 1000;
  }
  to {
    opacity: 1;
  }
}

.total-value {
  font-size: 1.75rem;
  font-weight: 700;
  fill: #111827;
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
}

:global(.dark) .total-value {
  fill: #f1f5f9;
}

.total-label {
  font-size: 0.75rem;
  fill: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

:global(.dark) .total-label {
  fill: #94a3b8;
}
</style>


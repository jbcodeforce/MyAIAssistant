<template>
  <div class="line-chart" ref="chartContainer">
    <div class="chart-y-axis">
      <span class="y-label">{{ maxValue }}</span>
      <span class="y-label">{{ Math.round(maxValue / 2) }}</span>
      <span class="y-label">0</span>
    </div>
    <div class="chart-area">
      <div class="grid-lines">
        <div class="grid-line"></div>
        <div class="grid-line"></div>
        <div class="grid-line"></div>
      </div>
      <svg 
        class="chart-svg" 
        :viewBox="`0 0 ${chartWidth} ${chartHeight}`"
        preserveAspectRatio="none"
      >
        <!-- Area fills -->
        <path
          v-for="(series, index) in seriesData"
          :key="`area-${index}`"
          :d="getAreaPath(series.points)"
          :fill="series.color"
          fill-opacity="0.1"
          class="area-path"
          :style="{ '--delay': index * 0.15 + 's' }"
        />
        <!-- Lines -->
        <path
          v-for="(series, index) in seriesData"
          :key="`line-${index}`"
          :d="getLinePath(series.points)"
          :stroke="series.color"
          stroke-width="2"
          fill="none"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="line-path"
          :style="{ '--delay': index * 0.15 + 's' }"
        />
        <!-- Data points -->
        <g v-for="(series, sIndex) in seriesData" :key="`points-${sIndex}`">
          <circle
            v-for="(point, pIndex) in series.points"
            :key="`point-${sIndex}-${pIndex}`"
            :cx="point.x"
            :cy="point.y"
            r="4"
            :fill="series.color"
            class="data-point"
            :style="{ '--delay': (sIndex * 0.15 + pIndex * 0.02) + 's' }"
          >
            <title>{{ series.label }}: {{ point.value }} ({{ point.date }})</title>
          </circle>
        </g>
      </svg>
      <div class="x-axis">
        <span 
          v-for="(label, index) in xLabels" 
          :key="index" 
          class="x-label"
        >
          {{ label }}
        </span>
      </div>
    </div>
    <!-- Legend -->
    <div class="chart-legend">
      <div 
        v-for="(series, index) in seriesData" 
        :key="`legend-${index}`"
        class="legend-item"
      >
        <span class="legend-line" :style="{ background: series.color }"></span>
        <span class="legend-label">{{ series.label }}</span>
        <span class="legend-value">{{ series.total }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    required: true,
    default: () => []
    // Expected format: [{ date: '2025-01-01', open: 3, started: 2, completed: 1, cancelled: 0 }, ...]
  },
  series: {
    type: Array,
    default: () => [
      { key: 'open', label: 'Open', color: '#6366f1' },
      { key: 'started', label: 'Started', color: '#f59e0b' },
      { key: 'completed', label: 'Completed', color: '#22c55e' },
      { key: 'cancelled', label: 'Cancelled', color: '#ef4444' }
    ]
  },
  maxValue: {
    type: Number,
    default: 10
  }
})

const chartContainer = ref(null)
const chartWidth = 800
const chartHeight = 200
const padding = { top: 10, right: 10, bottom: 10, left: 10 }

const seriesData = computed(() => {
  if (props.data.length === 0) return []
  
  const effectiveWidth = chartWidth - padding.left - padding.right
  const effectiveHeight = chartHeight - padding.top - padding.bottom
  
  return props.series.map(s => {
    const points = props.data.map((d, i) => {
      const x = padding.left + (props.data.length > 1 
        ? (i / (props.data.length - 1)) * effectiveWidth 
        : effectiveWidth / 2)
      const value = d[s.key] || 0
      const y = padding.top + effectiveHeight - (props.maxValue > 0 
        ? (value / props.maxValue) * effectiveHeight 
        : 0)
      return { x, y, value, date: d.date }
    })
    
    const total = props.data.reduce((sum, d) => sum + (d[s.key] || 0), 0)
    
    return {
      key: s.key,
      label: s.label,
      color: s.color,
      points,
      total
    }
  })
})

const xLabels = computed(() => {
  if (props.data.length === 0) return []
  if (props.data.length <= 7) {
    return props.data.map(d => formatDateLabel(d.date))
  }
  // Show fewer labels for longer datasets
  const step = Math.ceil(props.data.length / 6)
  return props.data
    .filter((_, i) => i % step === 0 || i === props.data.length - 1)
    .map(d => formatDateLabel(d.date))
})

function formatDateLabel(dateStr) {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function getLinePath(points) {
  if (points.length === 0) return ''
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`
  
  return points.reduce((path, point, i) => {
    if (i === 0) return `M ${point.x} ${point.y}`
    return `${path} L ${point.x} ${point.y}`
  }, '')
}

function getAreaPath(points) {
  if (points.length === 0) return ''
  
  const linePath = getLinePath(points)
  const firstX = points[0].x
  const lastX = points[points.length - 1].x
  const bottomY = chartHeight - padding.bottom
  
  return `${linePath} L ${lastX} ${bottomY} L ${firstX} ${bottomY} Z`
}
</script>

<style scoped>
.line-chart {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 0.75rem;
}

.chart-y-axis {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 28px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 36px;
  text-align: right;
  padding-right: 0.5rem;
}

.y-label {
  font-size: 0.75rem;
  color: #9ca3af;
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
}

:global(.dark) .y-label {
  color: #6b7280;
}

.chart-area {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  padding-left: 44px;
  min-height: 200px;
}

.grid-lines {
  position: absolute;
  top: 0;
  left: 44px;
  right: 0;
  bottom: 28px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  pointer-events: none;
}

.grid-line {
  height: 1px;
  background: #e5e7eb;
}

:global(.dark) .grid-line {
  background: #334155;
}

.chart-svg {
  flex: 1;
  width: 100%;
  min-height: 180px;
}

.line-path {
  animation: drawLine 1s ease-out forwards;
  animation-delay: var(--delay);
  stroke-dasharray: 2000;
  stroke-dashoffset: 2000;
}

@keyframes drawLine {
  to {
    stroke-dashoffset: 0;
  }
}

.area-path {
  animation: fadeIn 0.8s ease-out forwards;
  animation-delay: var(--delay);
  opacity: 0;
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}

.data-point {
  animation: pointAppear 0.3s ease-out forwards;
  animation-delay: var(--delay);
  opacity: 0;
  transform-origin: center;
  cursor: pointer;
  transition: r 0.15s ease;
}

.data-point:hover {
  r: 6;
}

@keyframes pointAppear {
  from {
    opacity: 0;
    transform: scale(0);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.x-axis {
  display: flex;
  justify-content: space-between;
  padding-top: 8px;
  min-height: 20px;
}

.x-label {
  font-size: 0.625rem;
  color: #6b7280;
  white-space: nowrap;
}

:global(.dark) .x-label {
  color: #9ca3af;
}

.chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
  padding-top: 0.5rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.legend-line {
  width: 16px;
  height: 3px;
  border-radius: 2px;
}

.legend-label {
  font-size: 0.75rem;
  color: #4b5563;
}

:global(.dark) .legend-label {
  color: #9ca3af;
}

.legend-value {
  font-size: 0.75rem;
  font-weight: 600;
  color: #111827;
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
}

:global(.dark) .legend-value {
  color: #f1f5f9;
}

@media (max-width: 768px) {
  .chart-legend {
    gap: 0.5rem;
  }
  
  .legend-item {
    font-size: 0.6875rem;
  }
}
</style>


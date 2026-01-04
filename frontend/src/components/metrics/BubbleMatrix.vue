<template>
  <div class="bubble-matrix">
    <svg 
      :width="width" 
      :height="height" 
      :viewBox="`0 0 ${width} ${height}`"
      class="matrix-svg"
    >
      <!-- Background gradient -->
      <defs>
        <linearGradient id="matrixBg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color: #f0f9ff; stop-opacity: 0.5" />
          <stop offset="100%" style="stop-color: #faf5ff; stop-opacity: 0.5" />
        </linearGradient>
        <filter id="bubbleShadow" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.15"/>
        </filter>
      </defs>

      <!-- Background -->
      <rect 
        :x="paddingLeft" 
        :y="paddingTop" 
        :width="chartWidth" 
        :height="chartHeight" 
        fill="url(#matrixBg)"
        rx="8"
      />

      <!-- Quadrant backgrounds -->
      <rect 
        :x="paddingLeft" 
        :y="paddingTop" 
        :width="chartWidth / 2" 
        :height="chartHeight / 2" 
        fill="rgba(234, 179, 8, 0.08)"
        class="quadrant neglected"
      />
      <rect 
        :x="paddingLeft + chartWidth / 2" 
        :y="paddingTop" 
        :width="chartWidth / 2" 
        :height="chartHeight / 2" 
        fill="rgba(34, 197, 94, 0.08)"
        class="quadrant aligned"
      />
      <rect 
        :x="paddingLeft" 
        :y="paddingTop + chartHeight / 2" 
        :width="chartWidth / 2" 
        :height="chartHeight / 2" 
        fill="rgba(99, 102, 241, 0.08)"
        class="quadrant optimal"
      />
      <rect 
        :x="paddingLeft + chartWidth / 2" 
        :y="paddingTop + chartHeight / 2" 
        :width="chartWidth / 2" 
        :height="chartHeight / 2" 
        fill="rgba(239, 68, 68, 0.08)"
        class="quadrant overinvested"
      />

      <!-- Grid lines -->
      <line 
        :x1="paddingLeft" 
        :y1="paddingTop + chartHeight / 2" 
        :x2="paddingLeft + chartWidth" 
        :y2="paddingTop + chartHeight / 2" 
        stroke="#cbd5e1"
        stroke-width="2"
        stroke-dasharray="6,4"
      />
      <line 
        :x1="paddingLeft + chartWidth / 2" 
        :y1="paddingTop" 
        :x2="paddingLeft + chartWidth / 2" 
        :y2="paddingTop + chartHeight" 
        stroke="#cbd5e1"
        stroke-width="2"
        stroke-dasharray="6,4"
      />

      <!-- Axis lines -->
      <line 
        :x1="paddingLeft" 
        :y1="paddingTop + chartHeight" 
        :x2="paddingLeft + chartWidth" 
        :y2="paddingTop + chartHeight" 
        stroke="#64748b"
        stroke-width="2"
      />
      <line 
        :x1="paddingLeft" 
        :y1="paddingTop" 
        :x2="paddingLeft" 
        :y2="paddingTop + chartHeight" 
        stroke="#64748b"
        stroke-width="2"
      />

      <!-- Y-axis tick marks and values -->
      <g v-for="tick in [0, 5, 10]" :key="'y-' + tick">
        <line 
          :x1="paddingLeft - 6" 
          :y1="paddingTop + ((10 - tick) / 10) * chartHeight" 
          :x2="paddingLeft" 
          :y2="paddingTop + ((10 - tick) / 10) * chartHeight" 
          stroke="#64748b"
          stroke-width="2"
        />
        <text 
          :x="paddingLeft - 12" 
          :y="paddingTop + ((10 - tick) / 10) * chartHeight + 4" 
          class="tick-label"
          text-anchor="end"
        >
          {{ tick }}
        </text>
      </g>

      <!-- X-axis tick marks and values -->
      <g v-for="tick in [0, 5, 10]" :key="'x-' + tick">
        <line 
          :x1="paddingLeft + (tick / 10) * chartWidth" 
          :y1="paddingTop + chartHeight" 
          :x2="paddingLeft + (tick / 10) * chartWidth" 
          :y2="paddingTop + chartHeight + 6" 
          stroke="#64748b"
          stroke-width="2"
        />
        <text 
          :x="paddingLeft + (tick / 10) * chartWidth" 
          :y="paddingTop + chartHeight + 20" 
          class="tick-label"
          text-anchor="middle"
        >
          {{ tick }}
        </text>
      </g>

      <!-- Quadrant labels -->
      <text 
        :x="paddingLeft + chartWidth * 0.25" 
        :y="paddingTop + 24" 
        class="quadrant-label neglected-text"
        text-anchor="middle"
      >
        NEGLECTED
      </text>
      <text 
        :x="paddingLeft + chartWidth * 0.75" 
        :y="paddingTop + 24" 
        class="quadrant-label aligned-text"
        text-anchor="middle"
      >
        ALIGNED
      </text>
      <text 
        :x="paddingLeft + chartWidth * 0.25" 
        :y="paddingTop + chartHeight - 12" 
        class="quadrant-label optimal-text"
        text-anchor="middle"
      >
        OPTIMAL LOW
      </text>
      <text 
        :x="paddingLeft + chartWidth * 0.75" 
        :y="paddingTop + chartHeight - 12" 
        class="quadrant-label overinvested-text"
        text-anchor="middle"
      >
        OVER-INVESTED
      </text>

      <!-- X-axis label -->
      <text 
        :x="paddingLeft + chartWidth / 2" 
        :y="height - 8" 
        class="axis-label"
        text-anchor="middle"
      >
        Time Spent →
      </text>

      <!-- Y-axis label -->
      <text 
        :x="20" 
        :y="paddingTop + chartHeight / 2" 
        class="axis-label"
        text-anchor="middle"
        :transform="`rotate(-90, 20, ${paddingTop + chartHeight / 2})`"
      >
        ← Importance
      </text>

      <!-- Bubbles -->
      <g 
        v-for="(bubble, index) in bubbles" 
        :key="bubble.key"
        class="bubble-group"
        :style="{ animationDelay: `${index * 50}ms` }"
      >
        <circle 
          :cx="bubble.x"
          :cy="bubble.y"
          :r="bubble.radius"
          :fill="bubble.color"
          :stroke="bubble.strokeColor"
          stroke-width="2"
          filter="url(#bubbleShadow)"
          class="bubble"
          @mouseenter="showTooltip(bubble, $event)"
          @mouseleave="hideTooltip"
        />
        <text 
          v-if="bubble.radius >= 15"
          :x="bubble.x"
          :y="bubble.y"
          :dy="bubble.radius >= 20 ? 4 : 3"
          class="bubble-label"
          text-anchor="middle"
          :font-size="bubble.radius >= 25 ? 10 : 8"
        >
          {{ getShortLabel(bubble.label) }}
        </text>
      </g>
    </svg>

    <!-- Tooltip -->
    <div 
      v-if="tooltip.visible" 
      class="tooltip"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
    >
      <div class="tooltip-title">{{ tooltip.label }}</div>
      <div class="tooltip-row">
        <span class="tooltip-key">Importance:</span>
        <span class="tooltip-value">{{ tooltip.importance }}/10</span>
      </div>
      <div class="tooltip-row">
        <span class="tooltip-key">Time Spent:</span>
        <span class="tooltip-value">{{ tooltip.timeSpent }}/10</span>
      </div>
      <div class="tooltip-category">{{ tooltip.category }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    required: true,
    default: () => []
  },
  width: {
    type: Number,
    default: 700
  },
  height: {
    type: Number,
    default: 480
  }
})

const paddingLeft = 90
const paddingRight = 40
const paddingTop = 50
const paddingBottom = 60
const chartWidth = computed(() => props.width - paddingLeft - paddingRight)
const chartHeight = computed(() => props.height - paddingTop - paddingBottom)

const tooltip = reactive({
  visible: false,
  x: 0,
  y: 0,
  label: '',
  importance: 0,
  timeSpent: 0,
  category: ''
})

// Category colors
const categoryColors = {
  'Relationships': { fill: 'rgba(236, 72, 153, 0.7)', stroke: '#ec4899' },
  'Health': { fill: 'rgba(34, 197, 94, 0.7)', stroke: '#22c55e' },
  'Personal': { fill: 'rgba(168, 85, 247, 0.7)', stroke: '#a855f7' },
  'Social': { fill: 'rgba(59, 130, 246, 0.7)', stroke: '#3b82f6' },
  'Career': { fill: 'rgba(249, 115, 22, 0.7)', stroke: '#f97316' },
  'Growth': { fill: 'rgba(20, 184, 166, 0.7)', stroke: '#14b8a6' },
  'Resources': { fill: 'rgba(234, 179, 8, 0.7)', stroke: '#eab308' },
  'Leisure': { fill: 'rgba(139, 92, 246, 0.7)', stroke: '#8b5cf6' },
  'Basic': { fill: 'rgba(100, 116, 139, 0.7)', stroke: '#64748b' }
}

const bubbles = computed(() => {
  if (!props.data || props.data.length === 0) return []

  const minRadius = 10
  const maxRadius = 35

  // Find max time spent for scaling
  const maxTimeSpent = Math.max(...props.data.map(d => d.timeSpent), 1)

  return props.data.map(item => {
    // Position: importance on Y (inverted), timeSpent on X
    const x = paddingLeft + (item.timeSpent / 10) * chartWidth.value
    const y = paddingTop + ((10 - item.importance) / 10) * chartHeight.value

    // Radius based on time spent
    const normalizedSize = item.timeSpent / maxTimeSpent
    const radius = minRadius + normalizedSize * (maxRadius - minRadius)

    const colors = categoryColors[item.category] || categoryColors['Basic']

    return {
      key: item.key,
      label: item.label,
      category: item.category,
      importance: item.importance,
      timeSpent: item.timeSpent,
      x,
      y,
      radius: Math.max(radius, minRadius),
      color: colors.fill,
      strokeColor: colors.stroke
    }
  })
})

function getShortLabel(label) {
  const shortLabels = {
    'Partner': 'PTR',
    'Family': 'FAM',
    'Friends': 'FRD',
    'Physical Health': 'PHY',
    'Mental Health': 'MNT',
    'Spirituality': 'SPI',
    'Community': 'COM',
    'Societal': 'SOC',
    'Job/Work': 'JOB',
    'Learning': 'LRN',
    'Finance': 'FIN',
    'Hobbies': 'HOB',
    'Online Entertainment': 'ONL',
    'Offline Entertainment': 'OFF',
    'Physiological Needs': 'NED',
    'Daily Activities': 'DAY'
  }
  return shortLabels[label] || label.substring(0, 3).toUpperCase()
}

function showTooltip(bubble, event) {
  tooltip.visible = true
  tooltip.label = bubble.label
  tooltip.importance = bubble.importance
  tooltip.timeSpent = bubble.timeSpent
  tooltip.category = bubble.category
  
  const rect = event.target.getBoundingClientRect()
  const parent = event.target.closest('.bubble-matrix').getBoundingClientRect()
  
  tooltip.x = rect.left - parent.left + rect.width / 2
  tooltip.y = rect.top - parent.top - 10
}

function hideTooltip() {
  tooltip.visible = false
}
</script>

<style scoped>
.bubble-matrix {
  position: relative;
  width: 100%;
  display: flex;
  justify-content: center;
}

.matrix-svg {
  max-width: 100%;
  height: auto;
}

.quadrant-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  fill: #94a3b8;
}

.tick-label {
  font-size: 11px;
  font-weight: 500;
  fill: #64748b;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}

.neglected-text {
  fill: #b45309;
}

.aligned-text {
  fill: #15803d;
}

.optimal-text {
  fill: #4f46e5;
}

.overinvested-text {
  fill: #b91c1c;
}

.axis-label {
  font-size: 12px;
  font-weight: 500;
  fill: #64748b;
}

.bubble-group {
  animation: bubbleIn 0.4s ease-out forwards;
  opacity: 0;
}

@keyframes bubbleIn {
  from {
    opacity: 0;
    transform: scale(0.5);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.bubble {
  cursor: pointer;
  transition: all 0.2s ease;
}

.bubble:hover {
  filter: url(#bubbleShadow) brightness(1.1);
  transform: scale(1.1);
}

.bubble-label {
  fill: white;
  font-weight: 700;
  pointer-events: none;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.tooltip {
  position: absolute;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.75rem 1rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  pointer-events: none;
  transform: translate(-50%, -100%);
  z-index: 100;
  min-width: 140px;
}

:global(.dark) .tooltip {
  background: #1e293b;
  border-color: #334155;
}

.tooltip-title {
  font-weight: 700;
  font-size: 0.9375rem;
  color: #1e1b4b;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 0.5rem;
}

:global(.dark) .tooltip-title {
  color: #e0e7ff;
  border-bottom-color: #334155;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.25rem;
}

.tooltip-key {
  font-size: 0.8125rem;
  color: #6b7280;
}

:global(.dark) .tooltip-key {
  color: #94a3b8;
}

.tooltip-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6366f1;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}

.tooltip-category {
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #e2e8f0;
}

:global(.dark) .tooltip-category {
  border-top-color: #334155;
  color: #64748b;
}

@media (max-width: 768px) {
  .bubble-matrix {
    overflow-x: auto;
  }
}
</style>


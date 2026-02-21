<template>
  <div class="bar-chart">
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
      <div class="bars-container" ref="barsContainer">
        <div
          v-for="(item, index) in data"
          :key="index"
          class="bar-wrapper"
          :title="`${item.label}: ${item.value}`"
        >
          <div
            class="bar"
            :class="{ 'custom-color': barColor }"
            :style="getBarStyle(item.value, index)"
          >
            <span v-if="item.value > 0" class="bar-value" :style="barColor ? { color: barColor } : {}">{{ item.value }}</span>
          </div>
          <span class="bar-label" :title="item.label">{{ truncateLabel(item.label) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  data: {
    type: Array,
    required: true,
    default: () => []
  },
  maxValue: {
    type: Number,
    default: 10
  },
  barColor: {
    type: String,
    default: null
  }
})

function getBarHeight(value) {
  if (props.maxValue === 0) return '0%'
  const percentage = (value / props.maxValue) * 100
  return `${Math.max(percentage, value > 0 ? 4 : 0)}%`
}

function getBarStyle(value, index) {
  const style = {
    height: getBarHeight(value),
    '--delay': index * 0.03 + 's'
  }
  if (props.barColor) {
    style.background = props.barColor
  }
  return style
}

function truncateLabel(label) {
  const maxLength = props.data.length <= 3 ? 25 : props.data.length <= 6 ? 18 : 12
  if (label.length <= maxLength) return label
  return label.substring(0, maxLength - 1) + '…'
}
</script>

<style scoped>
.bar-chart {
  display: flex;
  height: 100%;
  gap: 0.5rem;
}

.chart-y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-bottom: 50px;
  min-width: 36px;
  text-align: right;
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
}

.grid-lines {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 50px;
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

.bars-container {
  flex: 1;
  display: flex;
  align-items: flex-end;
  gap: 2px;
  padding-bottom: 50px;
  overflow-x: auto;
  scrollbar-width: thin;
}

.bar-wrapper {
  flex: 1;
  min-width: 20px;
  max-width: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

/* More space for fewer bars */
.bars-container:has(.bar-wrapper:nth-child(-n+5)) {
  gap: 12px;
  padding-bottom: 60px;
}

.bars-container:has(.bar-wrapper:nth-child(-n+5)) .bar-wrapper {
  max-width: 80px;
  min-width: 40px;
}

.bars-container:has(.bar-wrapper:nth-child(-n+5)) .bar {
  max-width: 60px;
  min-width: 30px;
}

.bar {
  width: 100%;
  min-width: 12px;
  max-width: 32px;
  background: linear-gradient(180deg, #6366f1 0%, #4f46e5 100%);
  border-radius: 4px 4px 0 0;
  position: relative;
  transition: background 0.2s;
  animation: barGrow 0.6s ease-out forwards;
  animation-delay: var(--delay);
  transform-origin: bottom;
  transform: scaleY(0);
  cursor: pointer;
}

@keyframes barGrow {
  from {
    transform: scaleY(0);
  }
  to {
    transform: scaleY(1);
  }
}

.bar:hover {
  background: linear-gradient(180deg, #818cf8 0%, #6366f1 100%);
}

.bar.custom-color:hover {
  filter: brightness(1.15);
}

:global(.dark) .bar {
  background: linear-gradient(180deg, #818cf8 0%, #6366f1 100%);
}

:global(.dark) .bar:hover {
  background: linear-gradient(180deg, #a5b4fc 0%, #818cf8 100%);
}

:global(.dark) .bar.custom-color:hover {
  filter: brightness(1.15);
}

.bar-value {
  position: absolute;
  top: -22px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.6875rem;
  font-weight: 600;
  color: #4f46e5;
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  white-space: nowrap;
}

:global(.dark) .bar-value {
  color: #a5b4fc;
}

.bar-label {
  position: absolute;
  bottom: -4px;
  font-size: 0.6875rem;
  color: #6b7280;
  margin-top: 6px;
  white-space: nowrap;
  transform: rotate(-40deg);
  transform-origin: top left;
  text-align: left;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

:global(.dark) .bar-label {
  color: #9ca3af;
}

/* Better spacing for fewer bars */
.bars-container:has(.bar-wrapper:nth-child(-n+5)) .bar-label {
  font-size: 0.75rem;
  bottom: -6px;
  max-width: 160px;
}

/* Hide labels when there are many bars */
.bars-container:has(.bar-wrapper:nth-child(n+15)) .bar-label {
  display: none;
}

.bars-container:has(.bar-wrapper:nth-child(n+15)) {
  padding-bottom: 8px;
}

@media (max-width: 768px) {
  .bar-wrapper {
    min-width: 16px;
  }

  .bar-label {
    display: none;
  }

  .bars-container {
    padding-bottom: 8px;
  }
}
</style>


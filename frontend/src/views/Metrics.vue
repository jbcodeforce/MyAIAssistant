<template>
  <div class="metrics-page">
    <div class="metrics-header">
      <div>
        <h2>Metrics Dashboard</h2>
        <p class="view-description">Track project and task progress over time</p>
      </div>
      <div class="header-controls">
        <select v-model="selectedPeriod" @change="loadMetrics" class="period-select">
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
        </select>
        <select v-model="selectedDays" @change="loadMetrics" class="days-select">
          <option :value="7">Last 7 days</option>
          <option :value="14">Last 14 days</option>
          <option :value="30">Last 30 days</option>
          <option :value="90">Last 90 days</option>
          <option :value="180">Last 6 months</option>
          <option :value="365">Last year</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading metrics...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadMetrics" class="btn-primary">Retry</button>
    </div>

    <div v-else class="metrics-content">
      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="summary-card projects-card">
          <div class="card-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <div class="card-content">
            <span class="card-value">{{ metricsStore.totalProjects }}</span>
            <span class="card-label">Total Projects</span>
          </div>
        </div>

        <div class="summary-card tasks-card">
          <div class="card-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 11l3 3L22 4"/>
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
            </svg>
          </div>
          <div class="card-content">
            <span class="card-value">{{ metricsStore.totalTasks }}</span>
            <span class="card-label">Total Tasks</span>
          </div>
        </div>

        <div class="summary-card completed-card">
          <div class="card-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          </div>
          <div class="card-content">
            <span class="card-value">{{ metricsStore.totalCompleted }}</span>
            <span class="card-label">Completed ({{ selectedDays }}d)</span>
          </div>
        </div>
      </div>

      <!-- Charts Grid -->
      <div class="charts-grid">
        <!-- Project Status Distribution -->
        <div class="chart-card">
          <h3 class="chart-title">Projects by Status</h3>
          <div class="donut-chart-container" v-if="metricsStore.projectsByStatus.length > 0">
            <DonutChart :data="projectChartData" :colors="projectColors" />
            <div class="chart-legend">
              <div 
                v-for="(item, index) in metricsStore.projectsByStatus" 
                :key="item.status"
                class="legend-item"
              >
                <span class="legend-dot" :style="{ background: projectColors[index % projectColors.length] }"></span>
                <span class="legend-label">{{ item.status }}</span>
                <span class="legend-value">{{ item.count }}</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-chart">
            <p>No projects yet</p>
          </div>
        </div>

        <!-- Task Status Distribution -->
        <div class="chart-card">
          <h3 class="chart-title">Tasks by Status</h3>
          <div class="donut-chart-container" v-if="metricsStore.tasksByStatus.length > 0">
            <DonutChart :data="taskChartData" :colors="taskColors" />
            <div class="chart-legend">
              <div 
                v-for="(item, index) in metricsStore.tasksByStatus" 
                :key="item.status"
                class="legend-item"
              >
                <span class="legend-dot" :style="{ background: taskColors[index % taskColors.length] }"></span>
                <span class="legend-label">{{ item.status }}</span>
                <span class="legend-value">{{ item.count }}</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-chart">
            <p>No tasks yet</p>
          </div>
        </div>

        <!-- Task Completion Over Time -->
        <div class="chart-card wide">
          <h3 class="chart-title">Tasks Completed Over Time</h3>
          <div class="bar-chart-container" v-if="metricsStore.completionDataPoints.length > 0">
            <BarChart :data="completionChartData" :maxValue="maxCompletionValue" />
          </div>
          <div v-else class="empty-chart">
            <p>No completed tasks in this period</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'
import DonutChart from '@/components/metrics/DonutChart.vue'
import BarChart from '@/components/metrics/BarChart.vue'

const metricsStore = useMetricsStore()

const selectedPeriod = ref('daily')
const selectedDays = ref(30)

const loading = computed(() => metricsStore.loading)
const error = computed(() => metricsStore.error)

const projectColors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444']
const taskColors = ['#6366f1', '#22c55e', '#eab308', '#ef4444']

const projectChartData = computed(() => {
  return metricsStore.projectsByStatus.map(item => ({
    label: item.status,
    value: item.count
  }))
})

const taskChartData = computed(() => {
  return metricsStore.tasksByStatus.map(item => ({
    label: item.status,
    value: item.count
  }))
})

const completionChartData = computed(() => {
  return metricsStore.completionDataPoints.map(item => ({
    label: formatDateLabel(item.date),
    value: item.count,
    fullDate: item.date
  }))
})

const maxCompletionValue = computed(() => {
  if (metricsStore.completionDataPoints.length === 0) return 0
  return Math.max(...metricsStore.completionDataPoints.map(d => d.count), 1)
})

function formatDateLabel(dateStr) {
  const date = new Date(dateStr)
  if (selectedPeriod.value === 'monthly') {
    return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
  } else if (selectedPeriod.value === 'weekly') {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

async function loadMetrics() {
  try {
    await metricsStore.fetchDashboardMetrics(selectedPeriod.value, selectedDays.value)
  } catch (err) {
    console.error('Failed to load metrics:', err)
  }
}

onMounted(() => {
  loadMetrics()
})
</script>

<style scoped>
.metrics-page {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  width: 100%;
  padding: 2rem;
}

:global(.dark) .metrics-page {
  background: #0f172a;
}

.metrics-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.metrics-header h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
}

:global(.dark) .metrics-header h2 {
  color: #f1f5f9;
}

.view-description {
  margin: 0;
  color: #6b7280;
  font-size: 1rem;
}

.header-controls {
  display: flex;
  gap: 0.75rem;
}

.period-select,
.days-select {
  padding: 0.5rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: white;
  color: #374151;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

:global(.dark) .period-select,
:global(.dark) .days-select {
  background: #1e293b;
  border-color: #334155;
  color: #e2e8f0;
}

.period-select:hover,
.days-select:hover {
  border-color: #3b82f6;
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

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p,
.error-state p {
  font-size: 1.125rem;
  color: #6b7280;
}

.btn-primary {
  background-color: #2563eb;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background-color: #1d4ed8;
}

/* Summary Cards */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: white;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  transition: transform 0.2s, box-shadow 0.2s;
}

:global(.dark) .summary-card {
  background: #1e293b;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

:global(.dark) .summary-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 12px;
  flex-shrink: 0;
}

.projects-card .card-icon {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #2563eb;
}

:global(.dark) .projects-card .card-icon {
  background: linear-gradient(135deg, #1e3a5f 0%, #1e40af 100%);
  color: #60a5fa;
}

.tasks-card .card-icon {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  color: #16a34a;
}

:global(.dark) .tasks-card .card-icon {
  background: linear-gradient(135deg, #14532d 0%, #166534 100%);
  color: #4ade80;
}

.completed-card .card-icon {
  background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
  color: #7c3aed;
}

:global(.dark) .completed-card .card-icon {
  background: linear-gradient(135deg, #4c1d95 0%, #5b21b6 100%);
  color: #a78bfa;
}

.card-content {
  display: flex;
  flex-direction: column;
}

.card-value {
  font-size: 2rem;
  font-weight: 700;
  color: #111827;
  line-height: 1.2;
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
}

:global(.dark) .card-value {
  color: #f1f5f9;
}

.card-label {
  font-size: 0.875rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

:global(.dark) .card-label {
  color: #94a3b8;
}

/* Charts Grid */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

@media (max-width: 1024px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

.chart-card {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
}

:global(.dark) .chart-card {
  background: #1e293b;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.chart-card.wide {
  grid-column: 1 / -1;
}

.chart-title {
  margin: 0 0 1.5rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
}

:global(.dark) .chart-title {
  color: #f1f5f9;
}

.donut-chart-container {
  display: flex;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
  justify-content: center;
}

.chart-legend {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}

.legend-label {
  font-size: 0.875rem;
  color: #4b5563;
  min-width: 100px;
}

:global(.dark) .legend-label {
  color: #9ca3af;
}

.legend-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
}

:global(.dark) .legend-value {
  color: #f1f5f9;
}

.bar-chart-container {
  height: 280px;
  width: 100%;
}

.empty-chart {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: #9ca3af;
  font-size: 0.9375rem;
}

@media (max-width: 768px) {
  .metrics-page {
    padding: 1rem;
  }

  .summary-cards {
    grid-template-columns: 1fr;
  }

  .donut-chart-container {
    flex-direction: column;
  }
}
</style>


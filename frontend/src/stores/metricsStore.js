import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { metricsApi } from '@/services/api'

export const useMetricsStore = defineStore('metrics', () => {
  // State
  const projectMetrics = ref(null)
  const taskMetrics = ref(null)
  const taskCompletion = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const totalProjects = computed(() => projectMetrics.value?.total || 0)
  const totalTasks = computed(() => taskMetrics.value?.total || 0)
  const totalCompleted = computed(() => taskCompletion.value?.total_completed || 0)

  const projectsByStatus = computed(() => {
    if (!projectMetrics.value?.by_status) return []
    return projectMetrics.value.by_status
  })

  const tasksByStatus = computed(() => {
    if (!taskMetrics.value?.by_status) return []
    return taskMetrics.value.by_status
  })

  const completionDataPoints = computed(() => {
    if (!taskCompletion.value?.data_points) return []
    return taskCompletion.value.data_points
  })

  // Actions
  async function fetchDashboardMetrics(period = 'daily', days = 30) {
    loading.value = true
    error.value = null
    try {
      const response = await metricsApi.getDashboard(period, days)
      const data = response.data
      projectMetrics.value = data.projects
      taskMetrics.value = data.tasks
      taskCompletion.value = data.tasks_completion
      return data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch metrics'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchProjectMetrics() {
    loading.value = true
    error.value = null
    try {
      const response = await metricsApi.getProjects()
      projectMetrics.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch project metrics'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchTaskMetrics() {
    loading.value = true
    error.value = null
    try {
      const response = await metricsApi.getTasks()
      taskMetrics.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch task metrics'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchTaskCompletion(period = 'daily', days = 30) {
    loading.value = true
    error.value = null
    try {
      const response = await metricsApi.getTaskCompletion(period, days)
      taskCompletion.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch task completion metrics'
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    projectMetrics,
    taskMetrics,
    taskCompletion,
    loading,
    error,
    // Getters
    totalProjects,
    totalTasks,
    totalCompleted,
    projectsByStatus,
    tasksByStatus,
    completionDataPoints,
    // Actions
    fetchDashboardMetrics,
    fetchProjectMetrics,
    fetchTaskMetrics,
    fetchTaskCompletion,
    clearError
  }
})


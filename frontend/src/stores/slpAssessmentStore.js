import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { slpAssessmentsApi } from '@/services/api'

/**
 * Life dimensions for SLP assessments
 */
export const LIFE_DIMENSIONS = [
  { key: 'partner', label: 'Partner', category: 'Relationships' },
  { key: 'family', label: 'Family', category: 'Relationships' },
  { key: 'friends', label: 'Friends', category: 'Relationships' },
  { key: 'physical_health', label: 'Physical Health', category: 'Health' },
  { key: 'mental_health', label: 'Mental Health', category: 'Health' },
  { key: 'spirituality', label: 'Spirituality', category: 'Personal' },
  { key: 'community', label: 'Community', category: 'Social' },
  { key: 'societal', label: 'Societal', category: 'Social' },
  { key: 'job_task', label: 'Job/Work', category: 'Career' },
  { key: 'learning', label: 'Learning', category: 'Growth' },
  { key: 'finance', label: 'Finance', category: 'Resources' },
  { key: 'hobbies', label: 'Hobbies', category: 'Leisure' },
  { key: 'online_entertainment', label: 'Online Entertainment', category: 'Leisure' },
  { key: 'offline_entertainment', label: 'Offline Entertainment', category: 'Leisure' },
  { key: 'physiological_needs', label: 'Physiological Needs', category: 'Basic' },
  { key: 'daily_activities', label: 'Daily Activities', category: 'Basic' }
]

export const useSlpAssessmentStore = defineStore('slpAssessments', () => {
  const assessments = ref([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref(null)

  // Get the latest assessment
  const latestAssessment = computed(() => {
    if (assessments.value.length === 0) return null
    return assessments.value[0]
  })

  // Transform assessment to bubble data for the matrix
  function assessmentToBubbleData(assessment) {
    if (!assessment) return []
    
    return LIFE_DIMENSIONS.map(dim => ({
      key: dim.key,
      label: dim.label,
      category: dim.category,
      importance: assessment[dim.key]?.importance || 0,
      timeSpent: assessment[dim.key]?.time_spent || 0
    }))
  }

  async function fetchAssessments(params = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await slpAssessmentsApi.list(params)
      assessments.value = response.data.assessments
      total.value = response.data.total
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to load assessments'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchAssessment(id) {
    loading.value = true
    error.value = null
    try {
      const response = await slpAssessmentsApi.get(id)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to load assessment'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createAssessment(assessment) {
    try {
      const response = await slpAssessmentsApi.create(assessment)
      assessments.value.unshift(response.data)
      total.value++
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create assessment'
      throw err
    }
  }

  async function updateAssessment(id, assessment) {
    try {
      const response = await slpAssessmentsApi.update(id, assessment)
      const index = assessments.value.findIndex(a => a.id === id)
      if (index !== -1) {
        assessments.value[index] = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update assessment'
      throw err
    }
  }

  async function deleteAssessment(id) {
    try {
      await slpAssessmentsApi.delete(id)
      assessments.value = assessments.value.filter(a => a.id !== id)
      total.value--
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to delete assessment'
      throw err
    }
  }

  return {
    assessments,
    total,
    loading,
    error,
    latestAssessment,
    assessmentToBubbleData,
    fetchAssessments,
    fetchAssessment,
    createAssessment,
    updateAssessment,
    deleteAssessment
  }
})


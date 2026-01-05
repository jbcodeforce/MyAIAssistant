import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { meetingRefsApi, organizationsApi, projectsApi } from '@/services/api'

export const useMeetingRefStore = defineStore('meetingRef', () => {
  const items = ref([])
  const loading = ref(false)
  const error = ref(null)
  const currentItem = ref(null)
  const currentContent = ref('')
  
  // Cache for organizations and projects
  const organizations = ref([])
  const projects = ref([])

  const itemsByOrg = computed(() => {
    const grouped = {}
    items.value.forEach(item => {
      const orgId = item.org_id || 'unassigned'
      if (!grouped[orgId]) grouped[orgId] = []
      grouped[orgId].push(item)
    })
    return grouped
  })

  const itemsByProject = computed(() => {
    const grouped = {}
    items.value.forEach(item => {
      const projectId = item.project_id || 'unassigned'
      if (!grouped[projectId]) grouped[projectId] = []
      grouped[projectId].push(item)
    })
    return grouped
  })

  async function fetchItems(params = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await meetingRefsApi.list(params)
      items.value = response.data.meeting_refs
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch meeting references'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getItem(id) {
    loading.value = true
    error.value = null
    try {
      const response = await meetingRefsApi.get(id)
      currentItem.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch meeting reference'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getContent(id) {
    loading.value = true
    error.value = null
    try {
      const response = await meetingRefsApi.getContent(id)
      currentContent.value = response.data.content
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch meeting content'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createItem(meetingRef) {
    loading.value = true
    error.value = null
    try {
      const response = await meetingRefsApi.create(meetingRef)
      items.value.unshift(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create meeting reference'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateItem(id, updates) {
    loading.value = true
    error.value = null
    try {
      const response = await meetingRefsApi.update(id, updates)
      const index = items.value.findIndex(item => item.id === id)
      if (index !== -1) {
        items.value[index] = response.data
      }
      if (currentItem.value?.id === id) {
        currentItem.value = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update meeting reference'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteItem(id) {
    loading.value = true
    error.value = null
    try {
      await meetingRefsApi.delete(id)
      items.value = items.value.filter(item => item.id !== id)
      if (currentItem.value?.id === id) {
        currentItem.value = null
        currentContent.value = ''
      }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to delete meeting reference'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchOrganizations() {
    try {
      const response = await organizationsApi.list({ limit: 500 })
      organizations.value = response.data.organizations
      return organizations.value
    } catch (err) {
      console.error('Failed to fetch organizations:', err)
      return []
    }
  }

  async function fetchProjects() {
    try {
      const response = await projectsApi.list({ limit: 500 })
      projects.value = response.data.projects
      return projects.value
    } catch (err) {
      console.error('Failed to fetch projects:', err)
      return []
    }
  }

  function getOrganizationName(orgId) {
    if (!orgId) return null
    const org = organizations.value.find(o => o.id === orgId)
    return org?.name || `Org #${orgId}`
  }

  function getProjectName(projectId) {
    if (!projectId) return null
    const project = projects.value.find(p => p.id === projectId)
    return project?.name || `Project #${projectId}`
  }

  function clearError() {
    error.value = null
  }

  function clearCurrent() {
    currentItem.value = null
    currentContent.value = ''
  }

  return {
    items,
    loading,
    error,
    currentItem,
    currentContent,
    organizations,
    projects,
    itemsByOrg,
    itemsByProject,
    fetchItems,
    getItem,
    getContent,
    createItem,
    updateItem,
    deleteItem,
    fetchOrganizations,
    fetchProjects,
    getOrganizationName,
    getProjectName,
    clearError,
    clearCurrent
  }
})


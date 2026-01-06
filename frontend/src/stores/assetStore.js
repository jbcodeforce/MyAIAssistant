import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { assetsApi, projectsApi, todosApi } from '@/services/api'

export const useAssetStore = defineStore('asset', () => {
  const items = ref([])
  const loading = ref(false)
  const error = ref(null)
  const currentItem = ref(null)
  
  // Cache for projects and todos
  const projects = ref([])
  const todos = ref([])

  const itemsByProject = computed(() => {
    const grouped = {}
    items.value.forEach(item => {
      const projectId = item.project_id || 'unassigned'
      if (!grouped[projectId]) grouped[projectId] = []
      grouped[projectId].push(item)
    })
    return grouped
  })

  const itemsByTodo = computed(() => {
    const grouped = {}
    items.value.forEach(item => {
      const todoId = item.todo_id || 'unassigned'
      if (!grouped[todoId]) grouped[todoId] = []
      grouped[todoId].push(item)
    })
    return grouped
  })

  async function fetchItems(params = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await assetsApi.list(params)
      items.value = response.data.assets
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch assets'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getItem(id) {
    loading.value = true
    error.value = null
    try {
      const response = await assetsApi.get(id)
      currentItem.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch asset'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createItem(asset) {
    loading.value = true
    error.value = null
    try {
      const response = await assetsApi.create(asset)
      items.value.unshift(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create asset'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateItem(id, updates) {
    loading.value = true
    error.value = null
    try {
      const response = await assetsApi.update(id, updates)
      const index = items.value.findIndex(item => item.id === id)
      if (index !== -1) {
        items.value[index] = response.data
      }
      if (currentItem.value?.id === id) {
        currentItem.value = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update asset'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteItem(id) {
    loading.value = true
    error.value = null
    try {
      await assetsApi.delete(id)
      items.value = items.value.filter(item => item.id !== id)
      if (currentItem.value?.id === id) {
        currentItem.value = null
      }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to delete asset'
      throw err
    } finally {
      loading.value = false
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

  async function fetchTodos() {
    try {
      const response = await todosApi.list({ limit: 500, status: 'Open,Started' })
      todos.value = response.data.todos
      return todos.value
    } catch (err) {
      console.error('Failed to fetch todos:', err)
      return []
    }
  }

  function getProjectName(projectId) {
    if (!projectId) return null
    const project = projects.value.find(p => p.id === projectId)
    return project?.name || `Project #${projectId}`
  }

  function getTodoTitle(todoId) {
    if (!todoId) return null
    const todo = todos.value.find(t => t.id === todoId)
    return todo?.title || `Task #${todoId}`
  }

  function clearError() {
    error.value = null
  }

  function clearCurrent() {
    currentItem.value = null
  }

  return {
    items,
    loading,
    error,
    currentItem,
    projects,
    todos,
    itemsByProject,
    itemsByTodo,
    fetchItems,
    getItem,
    createItem,
    updateItem,
    deleteItem,
    fetchProjects,
    fetchTodos,
    getProjectName,
    getTodoTitle,
    clearError,
    clearCurrent
  }
})


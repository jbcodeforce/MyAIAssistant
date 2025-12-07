import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { knowledgeApi } from '@/services/api'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const items = ref([])
  const loading = ref(false)
  const error = ref(null)
  const currentItem = ref(null)

  const activeItems = computed(() => 
    items.value.filter(item => item.status === 'active')
  )

  const archivedItems = computed(() => 
    items.value.filter(item => item.status === 'archived')
  )

  const markdownItems = computed(() => 
    items.value.filter(item => item.document_type === 'markdown')
  )

  const websiteItems = computed(() => 
    items.value.filter(item => item.document_type === 'website')
  )

  async function fetchItems(params = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await knowledgeApi.list(params)
      items.value = response.data.items
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch knowledge items'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getItem(id) {
    loading.value = true
    error.value = null
    try {
      const response = await knowledgeApi.get(id)
      currentItem.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch knowledge item'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createItem(knowledge) {
    loading.value = true
    error.value = null
    try {
      const response = await knowledgeApi.create(knowledge)
      items.value.unshift(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create knowledge item'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateItem(id, updates) {
    loading.value = true
    error.value = null
    try {
      const response = await knowledgeApi.update(id, updates)
      const index = items.value.findIndex(item => item.id === id)
      if (index !== -1) {
        items.value[index] = response.data
      }
      if (currentItem.value?.id === id) {
        currentItem.value = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update knowledge item'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteItem(id) {
    loading.value = true
    error.value = null
    try {
      await knowledgeApi.delete(id)
      items.value = items.value.filter(item => item.id !== id)
      if (currentItem.value?.id === id) {
        currentItem.value = null
      }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to delete knowledge item'
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    items,
    loading,
    error,
    currentItem,
    activeItems,
    archivedItems,
    markdownItems,
    websiteItems,
    fetchItems,
    getItem,
    createItem,
    updateItem,
    deleteItem,
    clearError
  }
})


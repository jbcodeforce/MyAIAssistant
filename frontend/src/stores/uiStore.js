import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', () => {
  const showCreateModal = ref(false)
  const showEditModal = ref(false)
  const selectedTodoId = ref(null)
  const activeView = ref('dashboard')

  function openCreateModal() {
    showCreateModal.value = true
  }

  function closeCreateModal() {
    showCreateModal.value = false
  }

  function openEditModal(todoId) {
    selectedTodoId.value = todoId
    showEditModal.value = true
  }

  function closeEditModal() {
    showEditModal.value = false
    selectedTodoId.value = null
  }

  function setActiveView(view) {
    activeView.value = view
  }

  return {
    showCreateModal,
    showEditModal,
    selectedTodoId,
    activeView,
    openCreateModal,
    closeCreateModal,
    openEditModal,
    closeEditModal,
    setActiveView
  }
})


import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { todosApi } from '@/services/api'

export const useTodoStore = defineStore('todo', () => {
  const todos = ref([])
  const loading = ref(false)
  const error = ref(null)
  const currentTodo = ref(null)

  const openTodos = computed(() => 
    todos.value.filter(todo => todo.status === 'Open')
  )

  const startedTodos = computed(() => 
    todos.value.filter(todo => todo.status === 'Started')
  )

  const completedTodos = computed(() => 
    todos.value.filter(todo => todo.status === 'Completed')
  )

  const urgentImportant = computed(() => 
    todos.value.filter(todo => 
      todo.urgency === 'Urgent' && todo.importance === 'Important'
    )
  )

  const urgentNotImportant = computed(() => 
    todos.value.filter(todo => 
      todo.urgency === 'Urgent' && todo.importance === 'Not Important'
    )
  )

  const notUrgentImportant = computed(() => 
    todos.value.filter(todo => 
      todo.urgency === 'Not Urgent' && todo.importance === 'Important'
    )
  )

  const notUrgentNotImportant = computed(() => 
    todos.value.filter(todo => 
      todo.urgency === 'Not Urgent' && todo.importance === 'Not Important'
    )
  )

  async function fetchTodos(params = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await todosApi.list(params)
      todos.value = response.data.todos
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch todos'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchTodosByQuadrant(urgency, importance) {
    loading.value = true
    error.value = null
    try {
      const response = await todosApi.listByQuadrant(urgency, importance)
      return response.data.todos
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch todos'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchUnclassifiedTodos(params = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await todosApi.listUnclassified(params)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch unclassified todos'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getTodo(id) {
    loading.value = true
    error.value = null
    try {
      const response = await todosApi.get(id)
      currentTodo.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch todo'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createTodo(todo) {
    loading.value = true
    error.value = null
    try {
      const response = await todosApi.create(todo)
      todos.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create todo'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateTodo(id, updates) {
    loading.value = true
    error.value = null
    try {
      const response = await todosApi.update(id, updates)
      const index = todos.value.findIndex(t => t.id === id)
      if (index !== -1) {
        todos.value[index] = response.data
      }
      if (currentTodo.value?.id === id) {
        currentTodo.value = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update todo'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteTodo(id) {
    loading.value = true
    error.value = null
    try {
      await todosApi.delete(id)
      todos.value = todos.value.filter(t => t.id !== id)
      if (currentTodo.value?.id === id) {
        currentTodo.value = null
      }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to delete todo'
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    todos,
    loading,
    error,
    currentTodo,
    openTodos,
    startedTodos,
    completedTodos,
    urgentImportant,
    urgentNotImportant,
    notUrgentImportant,
    notUrgentNotImportant,
    fetchTodos,
    fetchTodosByQuadrant,
    fetchUnclassifiedTodos,
    getTodo,
    createTodo,
    updateTodo,
    deleteTodo,
    clearError
  }
})


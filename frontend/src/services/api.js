import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export const todosApi = {
  list(params = {}) {
    return api.get('/todos/', { params })
  },

  get(id) {
    return api.get(`/todos/${id}`)
  },

  create(todo) {
    return api.post('/todos/', todo)
  },

  update(id, todo) {
    return api.put(`/todos/${id}`, todo)
  },

  delete(id) {
    return api.delete(`/todos/${id}`)
  },

  listUnclassified(params = {}) {
    return api.get('/todos/unclassified', { params })
  },

  listByQuadrant(urgency, importance, params = {}) {
    return api.get(`/todos/canvas/${urgency}/${importance}`, { params })
  },

  // Task Plan methods
  getTaskPlan(todoId) {
    return api.get(`/todos/${todoId}/plan`)
  },

  saveTaskPlan(todoId, content) {
    return api.put(`/todos/${todoId}/plan`, { content })
  },

  deleteTaskPlan(todoId) {
    return api.delete(`/todos/${todoId}/plan`)
  }
}

export const knowledgeApi = {
  list(params = {}) {
    return api.get('/knowledge/', { params })
  },

  get(id) {
    return api.get(`/knowledge/${id}`)
  },

  create(knowledge) {
    return api.post('/knowledge/', knowledge)
  },

  update(id, knowledge) {
    return api.put(`/knowledge/${id}`, knowledge)
  },

  delete(id) {
    return api.delete(`/knowledge/${id}`)
  }
}

export const ragApi = {
  indexItem(knowledgeId) {
    return api.post(`/rag/index/${knowledgeId}`)
  },

  indexAll(status = null) {
    const params = status ? { status } : {}
    return api.post('/rag/index-all', null, { params })
  },

  removeIndex(knowledgeId) {
    return api.delete(`/rag/index/${knowledgeId}`)
  },

  search(query, nResults = 5, category = null) {
    const params = { q: query, n: nResults }
    if (category) params.category = category
    return api.get('/rag/search', { params })
  },

  getStats() {
    return api.get('/rag/stats')
  }
}

export const customersApi = {
  list(params = {}) {
    return api.get('/customers/', { params })
  },

  get(id) {
    return api.get(`/customers/${id}`)
  },

  create(customer) {
    return api.post('/customers/', customer)
  },

  update(id, customer) {
    return api.put(`/customers/${id}`, customer)
  },

  delete(id) {
    return api.delete(`/customers/${id}`)
  }
}

export const projectsApi = {
  list(params = {}) {
    return api.get('/projects/', { params })
  },

  get(id) {
    return api.get(`/projects/${id}`)
  },

  create(project) {
    return api.post('/projects/', project)
  },

  update(id, project) {
    return api.put(`/projects/${id}`, project)
  },

  delete(id) {
    return api.delete(`/projects/${id}`)
  },

  getTodos(id, params = {}) {
    return api.get(`/projects/${id}/todos`, { params })
  }
}

export const chatApi = {
  /**
   * Send a message to chat about a specific todo task
   * @param {number} todoId - The ID of the todo
   * @param {string} message - The user's message
   * @param {Array} conversationHistory - Previous messages [{role, content}]
   * @param {boolean} useRag - Whether to use RAG for context
   */
  sendMessage(todoId, message, conversationHistory = [], useRag = true) {
    return api.post(`/chat/todo/${todoId}`, {
      message,
      conversation_history: conversationHistory,
      use_rag: useRag
    })
  },

  /**
   * Send a message to chat using RAG knowledge base
   * @param {string} message - The user's message
   * @param {Array} conversationHistory - Previous messages [{role, content}]
   * @param {number} nResults - Number of RAG results to use (1-10)
   */
  ragChat(message, conversationHistory = [], nResults = 5) {
    return api.post('/chat/rag', {
      message,
      conversation_history: conversationHistory,
      n_results: nResults
    })
  },

  getConfig() {
    return api.get('/chat/config')
  },

  healthCheck() {
    return api.get('/chat/health')
  }
}

export default api


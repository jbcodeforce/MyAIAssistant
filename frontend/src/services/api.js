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

export const organizationsApi = {
  list(params = {}) {
    return api.get('/organizations/', { params })
  },

  get(id) {
    return api.get(`/organizations/${id}`)
  },

  create(organization) {
    return api.post('/organizations/', organization)
  },

  update(id, organization) {
    return api.put(`/organizations/${id}`, organization)
  },

  delete(id) {
    return api.delete(`/organizations/${id}`)
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
    return api.post('/chat/generic', {
      message,
      conversation_history: conversationHistory,
      n_results: nResults
    })
  },

  healthCheck() {
    return api.get('/chat/health')
  }
}

export const slpAssessmentsApi = {
  list(params = {}) {
    return api.get('/slp-assessments/', { params })
  },

  get(id) {
    return api.get(`/slp-assessments/${id}`)
  },

  create(assessment) {
    return api.post('/slp-assessments/', assessment)
  },

  update(id, assessment) {
    return api.put(`/slp-assessments/${id}`, assessment)
  },

  delete(id) {
    return api.delete(`/slp-assessments/${id}`)
  }
}

export const meetingRefsApi = {
  list(params = {}) {
    return api.get('/meeting-refs/', { params })
  },

  get(id) {
    return api.get(`/meeting-refs/${id}`)
  },

  getContent(id) {
    return api.get(`/meeting-refs/${id}/content`)
  },

  getByMeetingId(meetingId) {
    return api.get('/meeting-refs/search/by-meeting-id', { params: { meeting_id: meetingId } })
  },

  create(meetingRef) {
    return api.post('/meeting-refs/', meetingRef)
  },

  update(id, meetingRef) {
    return api.put(`/meeting-refs/${id}`, meetingRef)
  },

  delete(id) {
    return api.delete(`/meeting-refs/${id}`)
  }
}

export const metricsApi = {
  /**
   * Get project metrics grouped by status
   */
  getProjects() {
    return api.get('/metrics/projects')
  },

  /**
   * Get task metrics grouped by status
   */
  getTasks() {
    return api.get('/metrics/tasks')
  },

  /**
   * Get task completion over time
   * @param {string} period - 'daily', 'weekly', or 'monthly'
   * @param {number} days - Number of days to look back (1-365)
   */
  getTaskCompletion(period = 'daily', days = 30) {
    return api.get('/metrics/tasks/completion', { params: { period, days } })
  },

  /**
   * Get all dashboard metrics in one call
   * @param {string} period - 'daily', 'weekly', or 'monthly'
   * @param {number} days - Number of days to look back (1-365)
   */
  getDashboard(period = 'daily', days = 30) {
    return api.get('/metrics/dashboard', { params: { period, days } })
  }
}

export default api

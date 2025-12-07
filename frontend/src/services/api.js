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

export default api


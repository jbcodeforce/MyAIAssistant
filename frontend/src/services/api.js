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

// When backend sets agent_service_url, frontend calls agent_service directly for chat and RAG search/stats/delete.
let _configPromise = null
export async function getConfig() {
  if (!_configPromise) _configPromise = api.get('/config').then(r => r.data)
  return _configPromise
}

export async function getAgentServiceUrl() {
  const c = await getConfig()
  return c.agent_service_url || null
}

/** User context from config (user_name, email) for chat request bodies. */
async function getUserContext() {
  const c = await getConfig()
  const out = {}
  if (c.user_name != null && c.user_name !== '') out.user_name = c.user_name
  if (c.email != null && c.email !== '') out.email = c.email
  return out
}

async function agentFetch(baseUrl, path, options = {}) {
  const url = `${baseUrl.replace(/\/$/, '')}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options
  })
  const text = await res.text()
  if (!res.ok) {
    let detail = res.statusText
    try {
      const j = JSON.parse(text)
      if (j.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
    } catch (_) {}
    const err = new Error(detail)
    err.response = { status: res.status, data: text }
    throw err
  }
  return text ? JSON.parse(text) : {}
}

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

export const weeklyTodosApi = {
  list(params = {}) {
    return api.get('/weekly-todos/', { params })
  },

  get(id) {
    return api.get(`/weekly-todos/${id}`)
  },

  create(payload) {
    return api.post('/weekly-todos/', payload)
  },

  update(id, payload) {
    return api.put(`/weekly-todos/${id}`, payload)
  },

  delete(id) {
    return api.delete(`/weekly-todos/${id}`)
  },

  getAllocations(weekKey) {
    return api.get('/weekly-todos/allocations', { params: { week_key: weekKey } })
  },

  getAllocation(weeklyTodoId, weekKey) {
    return api.get(`/weekly-todos/${weeklyTodoId}/allocations/${encodeURIComponent(weekKey)}`)
  },

  setAllocation(weeklyTodoId, weekKey, payload) {
    return api.put(`/weekly-todos/${weeklyTodoId}/allocations/${encodeURIComponent(weekKey)}`, payload)
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

  async removeIndex(knowledgeId) {
    const base = await getAgentServiceUrl()
    if (base) {
      const data = await agentFetch(base, `/rag/index/${knowledgeId}`, { method: 'DELETE' })
      return { data }
    }
    return api.delete(`/rag/index/${knowledgeId}`)
  },

  async search(query, nResults = 5, category = null) {
    const base = await getAgentServiceUrl()
    if (base) {
      const params = new URLSearchParams({ q: query, n: nResults })
      if (category) params.set('category', category)
      const data = await agentFetch(base, `/rag/search?${params}`)
      return { data }
    }
    const params = { q: query, n: nResults }
    if (category) params.category = category
    return api.get('/rag/search', { params })
  },

  async getStats() {
    const base = await getAgentServiceUrl()
    if (base) {
      const data = await agentFetch(base, '/rag/stats')
      return { data }
    }
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
  },

  getTodos(organizationId, params = {}) {
    return api.get(`/organizations/${organizationId}/todos`, { params })
  },

  /**
   * Export organization content, projects, and meeting notes to a markdown file
   * in the workspace docs folder. Returns { path, absolute_path }.
   */
  export(id) {
    return api.post(`/organizations/${id}/export`)
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
   * Send a message to chat about a specific todo task. When agent_service_url is set, 
   * fetches todo from backend then POSTs to agent-service /chat/todo.
   */
  async sendMessage(todoId, message, conversationHistory = [], useRag = true) {
    const base = await getAgentServiceUrl()
    if (base) {
      const todoRes = await api.get(`/todos/${todoId}`)
      const todo = todoRes.data
      const userCtx = await getUserContext()
      const data = await agentFetch(base, '/chat/todo', {
        method: 'POST',
        body: JSON.stringify({
          message,
          conversation_history: conversationHistory,
          use_rag: useRag,
          task_title: todo.title,
          task_description: todo.description ?? null,
          ...userCtx
        })
      })
      return { data }
    }
    return api.post(`/chat/todo/${todoId}`, {
      message,
      conversation_history: conversationHistory,
      use_rag: useRag
    })
  },

  /**
   * Send a message to a chat agent. When agentUrl (exposed_url) is set, POST to that URL; else when agent_service_url is set, POST to /agents/<agentName>/runs.
   * @param {string} [agentName='MainAgent'] - Agent name for the runs endpoint
   * @param {string} [agentUrl] - Optional exposed_url of the selected agent (takes precedence)
   */
  async genericChat(message, conversationHistory = [], nResults = 5, agentName = 'MainAgent', agentUrl = null) {
    if (agentUrl) {
      const data = await agentFetch(agentUrl, '', {
        method: 'POST',
        body: JSON.stringify({ message, conversation_history: conversationHistory })
      })
      return { data }
    }
    const base = await getAgentServiceUrl()
    if (base) {
      const userCtx = await getUserContext()
      const path = `/agents/${encodeURIComponent(agentName)}/runs`
      const data = await agentFetch(base, path, {
        method: 'POST',
        body: JSON.stringify({
          message,
          conversation_history: conversationHistory,
          ...userCtx
        })
      })
      return { data }
    }
    return api.post('/chat/generic', {
      message,
      conversation_history: conversationHistory,
      n_results: nResults
    })
  },

  /**
   * Stream generic chat response. When agentUrl (exposed_url) is set, POST to agentUrl/stream; else uses agent_service or backend.
   * @param {string} [agentName='MainAgent'] - Agent name (passed in body when using agent service)
   * @param {string} [agentUrl] - Optional exposed_url of the selected agent (takes precedence)
   */
  async genericChatStream(message, conversationHistory = [], onChunk, onDone, onError, agentName = 'MainAgent', agentUrl = null) {
    let url
    let body
    try {
      const userCtx = await getUserContext()
      if (agentUrl) {
        const streamUrl = agentUrl.replace(/\/$/, '') + '/stream'
        url = streamUrl
        body = { message, conversation_history: conversationHistory, agent_name: agentName, ...userCtx }
      } else {
        const base = await getAgentServiceUrl()
        if (base) {
          url = `${base.replace(/\/$/, '')}/chat/generic/stream`
          body = { message, conversation_history: conversationHistory, agent_name: agentName, ...userCtx }
        } else {
          url = `${api.defaults.baseURL || ''}/chat/generic/stream`
          body = { message, conversation_history: conversationHistory, n_results: 5 }
        }
      }
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      if (!response.ok) {
        const errBody = await response.text()
        let detail = response.statusText
        try {
          const j = JSON.parse(errBody)
          if (j.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
        } catch (_) {}
        onError(new Error(detail))
        return
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) continue
          try {
            const obj = JSON.parse(trimmed)
            if (obj.content != null) onChunk(obj.content)
            if (obj.done) {
              onDone(obj.context_used || [])
              return
            }
          } catch (e) {
            // skip malformed line
          }
        }
      }
      if (buffer.trim()) {
        try {
          const obj = JSON.parse(buffer.trim())
          if (obj.content != null) onChunk(obj.content)
          if (obj.done) {
            onDone(obj.context_used || [])
            return
          }
        } catch (_) {}
      }
      onDone([])
    } catch (err) {
      onError(err)
    }
  },

  /**
   * Send a message to the knowledge-base / RAG chat. Uses agent-service when agent_service_url is set (as generic chat).
   */
  async kbChat(message, conversationHistory = [], nResults = 5) {
    const base = await getAgentServiceUrl()
    if (base) {
      const userCtx = await getUserContext()
      const data = await agentFetch(base, '/chat/generic', {
        method: 'POST',
        body: JSON.stringify({
          message,
          conversation_history: conversationHistory,
          context: {},
          force_intent: null,
          ...userCtx
        })
      })
      return { data }
    }
    return api.post('/chat/kb', {
      message,
      conversation_history: conversationHistory,
      n_results: nResults
    })
  },

  /**
   * Stream knowledge-base / Assistant chat. When agentUrl is set, POST to agentUrl/stream; else uses agent_service or backend.
   * @param {string} [agentName='MainAgent'] - Agent name (in body when using agent service)
   * @param {string} [agentUrl] - Optional exposed_url of the selected agent (takes precedence)
   */
  async kbChatStream(message, conversationHistory = [], onChunk, onDone, onError, agentName = 'MainAgent', agentUrl = null) {
    let url
    let body
    try {
      const userCtx = await getUserContext()
      if (agentUrl) {
        const streamUrl = agentUrl.replace(/\/$/, '') + '/stream'
        url = streamUrl
        body = { message, conversation_history: conversationHistory, force_intent: 'knowledge_search', agent_name: agentName, ...userCtx }
      } else {
        const base = await getAgentServiceUrl()
        if (base) {
          url = `${base.replace(/\/$/, '')}/chat/generic/stream`
          body = { message, conversation_history: conversationHistory, force_intent: 'knowledge_search', agent_name: agentName, ...userCtx }
        } else {
          url = `${api.defaults.baseURL || ''}/chat/generic/stream`
          body = { message, conversation_history: conversationHistory, n_results: 5, force_intent: 'knowledge_search' }
        }
      }
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      if (!response.ok) {
        const errBody = await response.text()
        let detail = response.statusText
        try {
          const j = JSON.parse(errBody)
          if (j.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
        } catch (_) {}
        onError(new Error(detail))
        return
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) continue
          try {
            const obj = JSON.parse(trimmed)
            if (obj.content != null) onChunk(obj.content)
            if (obj.done) {
              onDone(obj.context_used || [])
              return
            }
          } catch (e) {
            // skip malformed line
          }
        }
      }
      if (buffer.trim()) {
        try {
          const obj = JSON.parse(buffer.trim())
          if (obj.content != null) onChunk(obj.content)
          if (obj.done) {
            onDone(obj.context_used || [])
            return
          }
        } catch (_) {}
      }
      onDone([])
    } catch (err) {
      onError(err)
    }
  },

  async healthCheck() {
    const base = await getAgentServiceUrl()
    if (base) {
      const data = await agentFetch(base, '/health')
      return { data }
    }
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
  },

  extract(id) {
    return api.post(`/meeting-refs/${id}/extract`)
  }
}

export const assetsApi = {
  list(params = {}) {
    return api.get('/assets/', { params })
  },

  get(id) {
    return api.get(`/assets/${id}`)
  },

  create(asset) {
    return api.post('/assets/', asset)
  },

  update(id, asset) {
    return api.put(`/assets/${id}`, asset)
  },

  delete(id) {
    return api.delete(`/assets/${id}`)
  }
}

export const personsApi = {
  list(params = {}) {
    return api.get('/persons/', { params })
  },

  get(id) {
    return api.get(`/persons/${id}`)
  },

  create(person) {
    return api.post('/persons/', person)
  },

  update(id, person) {
    return api.put(`/persons/${id}`, person)
  },

  delete(id) {
    return api.delete(`/persons/${id}`)
  }
}

export const agentsApi = {
  /**
   * List configured agents from agent service (GET myai/agents).
   * Returns array of { agent_name, description, path_to_config, default }.
   * Uses agent_service_url when set; otherwise returns empty array.
   */
  async list() {
    const base = await getAgentServiceUrl()
    if (base) {
      const data = await agentFetch(base, '/myai/agents', { method: 'GET' })
      const list = Array.isArray(data) ? data : (data?.data ?? [])
      return { data: list }
    }
    return { data: [] }
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
  },

  /**
   * Get organizations created over time
   * @param {string} period - 'daily', 'weekly', or 'monthly'
   * @param {number} days - Number of days to look back (1-365)
   */
  getOrganizationsCreated(period = 'daily', days = 30) {
    return api.get('/metrics/organizations/created', { params: { period, days } })
  },

  /**
   * Get meetings created over time
   * @param {string} period - 'daily', 'weekly', or 'monthly'
   * @param {number} days - Number of days to look back (1-365)
   */
  getMeetingsCreated(period = 'daily', days = 30) {
    return api.get('/metrics/meetings/created', { params: { period, days } })
  },

  /**
   * Get task status over time (Open, Started, Completed, Cancelled)
   * @param {string} period - 'daily', 'weekly', or 'monthly'
   * @param {number} days - Number of days to look back (1-365)
   */
  getTaskStatusOverTime(period = 'daily', days = 30) {
    return api.get('/metrics/tasks/status-over-time', { params: { period, days } })
  },

  /**
   * Get weekly todo time allocation metrics for current week
   */
  getWeeklyTodos() {
    return api.get('/metrics/weekly-todos')
  }
}

export default api

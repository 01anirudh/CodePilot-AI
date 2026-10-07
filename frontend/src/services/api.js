import axios from 'axios'

const RAW_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) ||
  (typeof import.meta !== 'undefined' && import.meta.env?.NEXT_PUBLIC_API_URL) ||
  (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_URL) ||
  'http://localhost:8000/api/v1'

export const BASE_URL = RAW_URL.replace(/\/+$/, '')

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('codepilot_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle 401 globally
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('codepilot_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ─── Auth ────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (email, password) => api.post('/auth/login', null, {
    params: { username: email, password },
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  }),
  loginForm: (email, password) => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    return api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  me: () => api.get('/auth/me'),
}

// ─── Repositories ─────────────────────────────────────────────────────────────
export const repoApi = {
  list: (skip = 0, limit = 20) => api.get('/repositories/', { params: { skip, limit } }),
  create: (data) => api.post('/repositories/', data),
  get: (id) => api.get(`/repositories/${id}`),
  delete: (id) => api.delete(`/repositories/${id}`),
}

// ─── Workflows ────────────────────────────────────────────────────────────────
export const workflowApi = {
  list: (skip = 0, limit = 20) => api.get('/workflows/', { params: { skip, limit } }),
  create: (data) => api.post('/workflows/', data),
  get: (id) => api.get(`/workflows/${id}`),
  getAgentRuns: (id) => api.get(`/workflows/${id}/agent-runs`),
  approve: (id, approved, comment) => api.post(`/workflows/${id}/approve`, { approved, comment }),
}

// ─── Agents ───────────────────────────────────────────────────────────────────
export const agentApi = {
  list: () => api.get('/agents/'),
  get: (id) => api.get(`/agents/${id}`),
  getRuns: (id, limit = 10) => api.get(`/agents/${id}/runs`, { params: { limit } }),
  search: (query, repositoryId, limit = 5) =>
    api.post('/agents/search', null, { params: { query, repository_id: repositoryId, limit } }),
}

// ─── GitHub ───────────────────────────────────────────────────────────────────
export const githubApi = {
  listPRs: (skip = 0, limit = 20) => api.get('/github/pull-requests', { params: { skip, limit } }),
  getPR: (id) => api.get(`/github/pull-requests/${id}`),
  approvePR: (id, approved, comment) => api.post(`/github/pull-requests/${id}/approve`, { approved, comment }),
}

// ─── Audit Logs ───────────────────────────────────────────────────────────────
export const auditApi = {
  list: (params) => api.get('/audit-logs/', { params }),
}

// ─── Production Task & Projects API ──────────────────────────────────────────
const API_ROOT = BASE_URL.replace(/\/api\/v1$/, '') + '/api'
export const taskApi = {
  createProject: (data) => api.post('/projects', data, { baseURL: API_ROOT }),
  listProjects: () => api.get('/projects', { baseURL: API_ROOT }),
  runAgent: (data) => api.post('/agents/run', data, { baseURL: API_ROOT }),
  getTask: (taskId) => api.get(`/tasks/${taskId}`, { baseURL: API_ROOT }),
  getTaskStatus: (taskId) => api.get(`/tasks/${taskId}/status`, { baseURL: API_ROOT }),
  approveTask: (taskId, approved, comment) => api.post(`/tasks/${taskId}/approve`, { approved, comment }, { baseURL: API_ROOT }),
  health: () => api.get('/health', { baseURL: API_ROOT }),
}


// ─── SSE Stream ───────────────────────────────────────────────────────────────
export const streamWorkflow = (workflowId, onMessage, onDone) => {
  const token = localStorage.getItem('codepilot_token')
  const url = `${BASE_URL}/workflows/${workflowId}/stream`
  const es = new EventSource(`${url}?token=${token}`)
  es.onmessage = (e) => {
    const data = JSON.parse(e.data)
    onMessage(data)
    if (data.done) { es.close(); onDone?.() }
  }
  es.onerror = () => { es.close(); onDone?.() }
  return () => es.close()
}

export default api

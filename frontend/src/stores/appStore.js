import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi, repoApi, workflowApi, agentApi } from '../services/api'

const useAppStore = create(
  persist(
    (set, get) => ({
      // ─── Auth State ─────────────────────────────────────────────────────────
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const res = await authApi.loginForm(email, password)
        const { access_token, user } = res.data
        localStorage.setItem('codepilot_token', access_token)
        set({ user, token: access_token, isAuthenticated: true })
        return user
      },

      register: async (data) => {
        const res = await authApi.register(data)
        return res.data
      },

      logout: () => {
        localStorage.removeItem('codepilot_token')
        set({ user: null, token: null, isAuthenticated: false })
      },

      fetchMe: async () => {
        try {
          const res = await authApi.me()
          set({ user: res.data, isAuthenticated: true })
        } catch {
          get().logout()
        }
      },

      // ─── Repositories ────────────────────────────────────────────────────────
      repositories: [],
      reposLoading: false,

      fetchRepositories: async () => {
        set({ reposLoading: true })
        try {
          const res = await repoApi.list()
          set({ repositories: res.data })
        } finally {
          set({ reposLoading: false })
        }
      },

      addRepository: async (data) => {
        const res = await repoApi.create(data)
        set((s) => ({ repositories: [res.data, ...s.repositories] }))
        return res.data
      },

      removeRepository: async (id) => {
        try {
          await repoApi.delete(id)
          set((s) => ({ repositories: s.repositories.filter((r) => r.id !== id) }))
        } catch (err) {
          console.error("Delete failed:", err)
          alert(err.response?.data?.detail || "Failed to delete repository")
        }
      },

      // ─── Workflows ───────────────────────────────────────────────────────────
      workflows: [],
      workflowsLoading: false,
      activeWorkflow: null,
      workflowLogs: [],

      fetchWorkflows: async () => {
        set({ workflowsLoading: true })
        try {
          const res = await workflowApi.list()
          set({ workflows: res.data })
        } finally {
          set({ workflowsLoading: false })
        }
      },

      createWorkflow: async (data) => {
        const res = await workflowApi.create(data)
        set((s) => ({ workflows: [res.data, ...s.workflows] }))
        return res.data
      },

      setActiveWorkflow: (wf) => set({ activeWorkflow: wf, workflowLogs: [] }),
      addWorkflowLog: (log) => set((s) => ({ workflowLogs: [...s.workflowLogs, log] })),

      approveWorkflow: async (id, approved, comment) => {
        const res = await workflowApi.approve(id, approved, comment)
        set((s) => ({
          workflows: s.workflows.map((w) => (w.id === id ? res.data : w)),
        }))
        return res.data
      },

      // ─── Agents ──────────────────────────────────────────────────────────────
      agents: [],
      agentsLoading: false,

      fetchAgents: async () => {
        set({ agentsLoading: true })
        try {
          const res = await agentApi.list()
          set({ agents: res.data })
        } finally {
          set({ agentsLoading: false })
        }
      },

      // ─── UI State ────────────────────────────────────────────────────────────
      sidebarCollapsed: false,
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

      notifications: [],
      addNotification: (n) =>
        set((s) => ({ notifications: [{ id: Date.now(), ...n }, ...s.notifications].slice(0, 10) })),
      clearNotification: (id) =>
        set((s) => ({ notifications: s.notifications.filter((n) => n.id !== id) })),
    }),
    {
      name: 'codepilot-store',
      partialize: (s) => ({ token: s.token, user: s.user, isAuthenticated: s.isAuthenticated }),
    }
  )
)

export default useAppStore

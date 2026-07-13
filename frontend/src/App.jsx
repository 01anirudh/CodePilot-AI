import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { useEffect } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Repositories from './pages/Repositories'
import Workflows from './pages/Workflows'
import Agents from './pages/Agents'
import Review from './pages/Review'
import AuditLogs from './pages/AuditLogs'
import Settings from './pages/Settings'
import Login from './pages/Login'
import useAppStore from './stores/appStore'

function ProtectedLayout() {
  const { isAuthenticated, fetchMe } = useAppStore()

  useEffect(() => {
    const token = localStorage.getItem('codepilot_token')
    if (token) fetchMe()
  }, [])

  if (!isAuthenticated) return <Navigate to="/login" replace />

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-content">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/repositories" element={<Repositories />} />
          <Route path="/workflows" element={<Workflows />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/review" element={<Review />} />
          <Route path="/audit-logs" element={<AuditLogs />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

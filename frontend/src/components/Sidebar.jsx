import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, GitBranch, Workflow, Bot,
  ClipboardCheck, ScrollText, Settings, LogOut,
  ChevronLeft, ChevronRight, Zap,
} from 'lucide-react'
import useAppStore from '../stores/appStore'
import './Sidebar.css'

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/repositories', icon: GitBranch, label: 'Repositories' },
  { to: '/workflows', icon: Workflow, label: 'Workflows' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/review', icon: ClipboardCheck, label: 'Review' },
  { to: '/audit-logs', icon: ScrollText, label: 'Audit Logs' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  const { user, logout, sidebarCollapsed, toggleSidebar } = useAppStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-icon">
          <Zap size={20} />
        </div>
        {!sidebarCollapsed && (
          <div className="logo-text">
            <span className="logo-name gradient-text">CodePilot</span>
            <span className="logo-tag">AI Platform</span>
          </div>
        )}
        <button className="collapse-btn btn btn-ghost btn-icon" onClick={toggleSidebar}>
          {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            title={sidebarCollapsed ? label : undefined}
          >
            <Icon size={20} className="nav-icon" />
            {!sidebarCollapsed && <span className="nav-label">{label}</span>}
            {!sidebarCollapsed && <span className="nav-active-indicator" />}
          </NavLink>
        ))}
      </nav>

      {/* User Footer */}
      <div className="sidebar-footer">
        {user && (
          <div className="user-info">
            <div className="user-avatar">
              {user.avatar_url ? (
                <img src={user.avatar_url} alt={user.username} />
              ) : (
                <span>{(user.full_name || user.username || 'U')[0].toUpperCase()}</span>
              )}
            </div>
            {!sidebarCollapsed && (
              <div className="user-details">
                <span className="user-name">{user.full_name || user.username}</span>
                <span className="user-role badge badge-brand">{user.role}</span>
              </div>
            )}
          </div>
        )}
        <button
          className="btn btn-ghost btn-icon logout-btn"
          onClick={handleLogout}
          title="Logout"
        >
          <LogOut size={18} />
        </button>
      </div>
    </aside>
  )
}

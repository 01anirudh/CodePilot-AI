import { useEffect, useState } from 'react'
import {
  GitBranch, Workflow, Bot, CheckCircle, Clock,
  TrendingUp, Activity, Zap, ArrowRight, Star
} from 'lucide-react'
import { AreaChart, Area, ResponsiveContainer, Tooltip } from 'recharts'
import { Link } from 'react-router-dom'
import KPICard from '../components/KPICard'
import WorkflowPipeline from '../components/WorkflowPipeline'
import useAppStore from '../stores/appStore'
import './Dashboard.css'
import '../components/KPICard.css'

const MOCK_ACTIVITY = Array.from({ length: 7 }, (_, i) => ({
  day: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i],
  workflows: Math.floor(Math.random() * 12) + 2,
  bugs: Math.floor(Math.random() * 6) + 1,
}))

const RECENT_WORKFLOW_MOCK = [
  { id: '1', task: 'Fix authentication JWT bug', status: 'completed', repo: 'api-service', time: '2h ago', score: 89 },
  { id: '2', task: 'Add user profile endpoint', status: 'running', repo: 'backend', time: '15m ago', score: null },
  { id: '3', task: 'Generate unit tests for PaymentService', status: 'awaiting_approval', repo: 'payments', time: '1h ago', score: 92 },
  { id: '4', task: 'Refactor database queries', status: 'completed', repo: 'data-layer', time: '5h ago', score: 76 },
]

const STATUS_BADGE = {
  completed: 'badge-success',
  running: 'badge-info',
  awaiting_approval: 'badge-warning',
  failed: 'badge-error',
  queued: 'badge-muted',
}

export default function Dashboard() {
  const { user, repositories, workflows, fetchRepositories, fetchWorkflows } = useAppStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const init = async () => {
      try {
        await Promise.all([fetchRepositories(), fetchWorkflows()])
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  const completedWorkflows = workflows.filter(w => w.status === 'completed').length
  const runningWorkflows = workflows.filter(w => w.status === 'running').length

  return (
    <div className="dashboard animate-fade-up">
      {/* Hero Header */}
      <div className="dashboard-hero">
        <div className="hero-text">
          <h1>
            Welcome back, <span className="gradient-text">{user?.full_name?.split(' ')[0] || user?.username || 'Developer'}</span> 👋
          </h1>
          <p className="hero-subtitle">
            Your autonomous software engineering platform is ready.
            {runningWorkflows > 0 && ` ${runningWorkflows} workflow${runningWorkflows > 1 ? 's' : ''} running.`}
          </p>
        </div>
        <div className="hero-actions">
          <Link to="/workflows" className="btn btn-primary">
            <Zap size={16} />
            New Workflow
          </Link>
          <Link to="/repositories" className="btn btn-secondary">
            <GitBranch size={16} />
            Add Repository
          </Link>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid-4" style={{ marginBottom: '2rem' }}>
        <KPICard
          title="Repositories"
          value={loading ? '–' : repositories.length}
          subtitle="Connected repos"
          icon={GitBranch}
          color="#6366f1"
          trend="up"
          trendValue="+2 this week"
          loading={loading}
        />
        <KPICard
          title="Workflows Run"
          value={loading ? '–' : workflows.length}
          subtitle={`${completedWorkflows} completed`}
          icon={Workflow}
          color="#06b6d4"
          trend="up"
          trendValue="+12%"
          loading={loading}
        />
        <KPICard
          title="Agents Active"
          value="9"
          subtitle="All systems operational"
          icon={Bot}
          color="#10b981"
          trend="up"
          trendValue="100% uptime"
        />
        <KPICard
          title="Avg Review Score"
          value="84"
          subtitle="Out of 100"
          icon={Star}
          color="#f59e0b"
          trend="up"
          trendValue="+3 pts"
        />
      </div>

      {/* Main Grid */}
      <div className="dashboard-main-grid">
        {/* Activity Chart */}
        <div className="card chart-card">
          <div className="card-header-row">
            <div>
              <h3>Workflow Activity</h3>
              <p className="text-muted">Last 7 days</p>
            </div>
            <span className="badge badge-info">
              <Activity size={12} />
              Live
            </span>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={MOCK_ACTIVITY}>
              <defs>
                <linearGradient id="wfGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="bugGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Tooltip
                contentStyle={{ background: '#13131f', border: '1px solid #2a2a42', borderRadius: '8px', color: '#f1f1f8' }}
              />
              <Area type="monotone" dataKey="workflows" stroke="#6366f1" strokeWidth={2} fill="url(#wfGrad)" name="Workflows" />
              <Area type="monotone" dataKey="bugs" stroke="#06b6d4" strokeWidth={2} fill="url(#bugGrad)" name="Bugs Fixed" />
            </AreaChart>
          </ResponsiveContainer>
          <div className="chart-legend">
            <span className="legend-item"><span className="legend-dot" style={{ background: '#6366f1' }} />Workflows</span>
            <span className="legend-item"><span className="legend-dot" style={{ background: '#06b6d4' }} />Bugs Fixed</span>
          </div>
        </div>

        {/* Recent Workflows */}
        <div className="card">
          <div className="card-header-row">
            <h3>Recent Workflows</h3>
            <Link to="/workflows" className="btn btn-ghost btn-sm">
              View all <ArrowRight size={14} />
            </Link>
          </div>
          <div className="recent-list">
            {RECENT_WORKFLOW_MOCK.map(wf => (
              <div key={wf.id} className="recent-item">
                <div className="recent-item-info">
                  <span className={`badge ${STATUS_BADGE[wf.status] || 'badge-muted'}`}>
                    {wf.status.replace('_', ' ')}
                  </span>
                  <p className="recent-task">{wf.task}</p>
                  <p className="recent-meta">
                    <GitBranch size={12} />
                    {wf.repo} · {wf.time}
                  </p>
                </div>
                {wf.score !== null && (
                  <div className="recent-score">
                    <span>{wf.score}</span>
                    <span className="score-label">score</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Agent Pipeline Demo */}
      <div className="card pipeline-showcase">
        <div className="card-header-row">
          <div>
            <h3>Agent Pipeline</h3>
            <p className="text-muted">Live orchestration view</p>
          </div>
          <Link to="/agents" className="btn btn-secondary btn-sm">
            Manage Agents <ArrowRight size={14} />
          </Link>
        </div>
        <WorkflowPipeline
          completedSteps={['analyzer', 'knowledge', 'planner', 'codegen']}
          currentAgent="testing"
          errors={[]}
        />
        <div className="pipeline-status-row">
          <span className="badge badge-info">
            <span className="dot dot-info animate-pulse-ring" />
            Testing agent is running
          </span>
          <span className="text-muted" style={{ fontSize: '0.8125rem' }}>
            4 / 9 agents completed
          </span>
        </div>
      </div>
    </div>
  )
}

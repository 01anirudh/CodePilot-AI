import { useEffect, useState } from 'react'
import { Plus, Workflow, Play, CheckCircle2, Clock, XCircle, ChevronDown, ChevronUp } from 'lucide-react'
import useAppStore from '../stores/appStore'
import WorkflowPipeline from '../components/WorkflowPipeline'
import StreamingLog from '../components/StreamingLog'
import { workflowApi } from '../services/api'
import './Workflows.css'

const WORKFLOW_TYPES = [
  { value: 'full', label: '🚀 Full Pipeline', desc: 'All 9 agents — end to end' },
  { value: 'bug_fix', label: '🐛 Bug Fix', desc: 'Analyze, fix, test, and PR' },
  { value: 'generate_tests', label: '🧪 Generate Tests', desc: 'Write test suite' },
  { value: 'generate_docs', label: '📚 Generate Docs', desc: 'README, API docs, UML' },
  { value: 'code_review', label: '👁️ Code Review', desc: 'Security & quality review' },
  { value: 'refactor', label: '🔧 Refactor', desc: 'Improve code quality' },
  { value: 'analyze', label: '🔍 Analyze', desc: 'Repository analysis only' },
]

const STATUS_CONFIG = {
  queued:            { icon: <Clock size={16} />, cls: 'badge-muted',    label: 'Queued' },
  running:           { icon: <Play size={16} />, cls: 'badge-info',      label: 'Running' },
  awaiting_approval: { icon: <Clock size={16} />, cls: 'badge-warning',  label: 'Awaiting Approval' },
  completed:         { icon: <CheckCircle2 size={16} />, cls: 'badge-success', label: 'Completed' },
  failed:            { icon: <XCircle size={16} />, cls: 'badge-error',  label: 'Failed' },
  rejected:          { icon: <XCircle size={16} />, cls: 'badge-error',  label: 'Rejected' },
}

export default function Workflows() {
  const { repositories, workflows, workflowsLoading, fetchWorkflows, fetchRepositories, createWorkflow, approveWorkflow } = useAppStore()
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ repository_id: '', task_description: '', workflow_type: 'full' })
  const [creating, setCreating] = useState(false)
  const [expanded, setExpanded] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchWorkflows()
    fetchRepositories()
    const interval = setInterval(fetchWorkflows, 10000)
    return () => clearInterval(interval)
  }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreating(true)
    setError('')
    try {
      const wf = await createWorkflow(form)
      setShowCreate(false)
      setExpanded(wf.id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create workflow')
    } finally {
      setCreating(false)
    }
  }

  const handleApprove = async (wfId, approved) => {
    await approveWorkflow(wfId, approved, '')
    fetchWorkflows()
  }

  return (
    <div className="workflows animate-fade-up">
      <div className="page-header">
        <div>
          <h1>Workflows</h1>
          <p className="text-muted">Create and monitor multi-agent AI workflows</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={16} /> New Workflow
        </button>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal card workflow-modal" onClick={e => e.stopPropagation()}>
            <h3>Create Workflow</h3>
            <p className="text-muted" style={{ marginBottom: '1.5rem' }}>
              Describe what you want the AI to do with your code.
            </p>
            <form onSubmit={handleCreate} className="add-form">
              <div className="input-group">
                <label className="input-label">Repository *</label>
                <select
                  className="input"
                  value={form.repository_id}
                  onChange={e => setForm(f => ({ ...f, repository_id: e.target.value }))}
                  required
                >
                  <option value="">Select a repository...</option>
                  {repositories.map(r => (
                    <option key={r.id} value={r.id}>{r.full_name || r.name}</option>
                  ))}
                </select>
              </div>
              <div className="input-group">
                <label className="input-label">Task Description *</label>
                <textarea
                  className="input"
                  rows={3}
                  placeholder="e.g. Fix the login authentication bug and add comprehensive tests"
                  value={form.task_description}
                  onChange={e => setForm(f => ({ ...f, task_description: e.target.value }))}
                  required
                  style={{ resize: 'vertical' }}
                />
              </div>
              <div className="input-group">
                <label className="input-label">Workflow Type</label>
                <div className="workflow-type-grid">
                  {WORKFLOW_TYPES.map(t => (
                    <button
                      key={t.value}
                      type="button"
                      className={`type-option ${form.workflow_type === t.value ? 'selected' : ''}`}
                      onClick={() => setForm(f => ({ ...f, workflow_type: t.value }))}
                    >
                      <span className="type-label">{t.label}</span>
                      <span className="type-desc">{t.desc}</span>
                    </button>
                  ))}
                </div>
              </div>
              {error && <div className="alert alert-error">{error}</div>}
              <div className="form-actions">
                <button type="button" className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={creating}>
                  {creating ? 'Starting...' : '🚀 Start Workflow'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Workflow List */}
      {workflowsLoading && workflows.length === 0 ? (
        <div className="loading-placeholder">Loading workflows...</div>
      ) : workflows.length === 0 ? (
        <div className="empty-state card">
          <Workflow size={48} />
          <h3>No workflows yet</h3>
          <p>Create your first workflow to start automating your engineering tasks.</p>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            <Plus size={16} /> Create Workflow
          </button>
        </div>
      ) : (
        <div className="workflow-list">
          {workflows.map(wf => (
            <WorkflowCard
              key={wf.id}
              workflow={wf}
              expanded={expanded === wf.id}
              onToggle={() => setExpanded(expanded === wf.id ? null : wf.id)}
              onApprove={handleApprove}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function WorkflowCard({ workflow, expanded, onToggle, onApprove }) {
  const sc = STATUS_CONFIG[workflow.status] || STATUS_CONFIG.queued
  const result = workflow.result || {}
  const completedSteps = result.completed_steps || []
  const currentAgent = result.current_agent || ''
  const logs = result.logs || []

  return (
    <div className={`card workflow-card ${expanded ? 'expanded' : ''}`}>
      <div className="workflow-card-header" onClick={onToggle}>
        <div className="wf-header-left">
          <span className={`badge ${sc.cls}`}>{sc.icon}{sc.label}</span>
          <div>
            <p className="wf-task">{workflow.task_description || 'No description'}</p>
            <p className="wf-meta">
              {workflow.type} · {new Date(workflow.created_at).toLocaleDateString()}
              {workflow.plan && ` · ${workflow.plan.complexity || 'medium'} complexity`}
            </p>
          </div>
        </div>
        <button className="btn btn-ghost btn-icon">
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {expanded && (
        <div className="workflow-card-body">
          <div className="divider" />
          <WorkflowPipeline
            completedSteps={completedSteps}
            currentAgent={currentAgent}
            errors={result.errors || []}
          />

          {logs.length > 0 && <StreamingLog logs={logs} title="Execution Log" />}

          {/* Plan */}
          {workflow.plan && (
            <div className="wf-plan-box">
              <h4>Execution Plan</h4>
              <p className="text-muted">{workflow.plan.task_summary}</p>
              {workflow.plan.steps?.slice(0, 4).map(step => (
                <div key={step.step} className="plan-step">
                  <span className="step-num">{step.step}</span>
                  <span className="step-agent">[{step.agent}]</span>
                  <span className="step-action">{step.action}</span>
                </div>
              ))}
            </div>
          )}

          {/* GitHub Result */}
          {result.github_result?.pr_url && (
            <div className="alert alert-success">
              🐙 Pull Request: <a href={result.github_result.pr_url} target="_blank" rel="noreferrer">{result.github_result.pr_url}</a>
              {result.github_result.simulated && ' (simulated — add GITHUB_TOKEN to create real PR)'}
            </div>
          )}

          {/* Approval */}
          {workflow.status === 'awaiting_approval' && (
            <div className="approval-section">
              <div className="approval-header">
                <h4>👤 Human Approval Required</h4>
                <p className="text-muted">Review the generated code and plan before creating the pull request</p>
              </div>
              <div className="approval-actions">
                <button
                  className="btn btn-danger"
                  onClick={() => onApprove(workflow.id, false)}
                >
                  ✕ Reject
                </button>
                <button
                  className="btn btn-primary"
                  onClick={() => onApprove(workflow.id, true)}
                >
                  ✓ Approve & Create PR
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

import { useEffect, useState, useRef } from 'react'
import { createPortal } from 'react-dom'
import { Plus, Workflow, Play, CheckCircle2, Clock, XCircle, ChevronDown, ChevronUp } from 'lucide-react'
import useAppStore from '../stores/appStore'
import WorkflowPipeline from '../components/WorkflowPipeline'
import StreamingLog from '../components/StreamingLog'
import { workflowApi, BASE_URL } from '../services/api'
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
  queued:               { icon: <Clock size={16} />, cls: 'badge-muted',    label: 'Queued' },
  running:              { icon: <Play size={16} />, cls: 'badge-info',      label: 'Running' },
  analyzing:            { icon: <Clock size={16} />, cls: 'badge-info',     label: 'Analyzing' },
  planning:             { icon: <Clock size={16} />, cls: 'badge-info',     label: 'Planning' },
  coding:               { icon: <Play size={16} />, cls: 'badge-info',      label: 'Coding' },
  testing:              { icon: <Play size={16} />, cls: 'badge-info',      label: 'Testing' },
  reviewing:            { icon: <Clock size={16} />, cls: 'badge-info',     label: 'Reviewing' },
  waiting_for_approval: { icon: <Clock size={16} />, cls: 'badge-warning',  label: 'Waiting for Approval' },
  awaiting_approval:    { icon: <Clock size={16} />, cls: 'badge-warning',  label: 'Awaiting Approval' },
  completed:            { icon: <CheckCircle2 size={16} />, cls: 'badge-success', label: 'Completed' },
  failed:               { icon: <XCircle size={16} />, cls: 'badge-error',  label: 'Failed' },
  rejected:             { icon: <XCircle size={16} />, cls: 'badge-error',  label: 'Rejected' },
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

      {/* Create Modal — rendered via portal directly in document.body to avoid stacking context issues */}
      {showCreate && createPortal(
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal workflow-modal" onClick={e => e.stopPropagation()}>
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
        </div>,
        document.body
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
  const statusKey = (workflow.status || 'queued').toLowerCase()
  const sc = STATUS_CONFIG[statusKey] || STATUS_CONFIG.queued
  const result = workflow.result || {}
  
  const [liveLogs, setLiveLogs] = useState(result.logs || [])
  const [isStreaming, setIsStreaming] = useState(false)
  const abortControllerRef = useRef(null)

  useEffect(() => {
    // Only stream if expanded and not in a terminal state
    const isTerminal = ['completed', 'failed', 'rejected', 'waiting_for_approval', 'awaiting_approval'].includes(statusKey)
    if (expanded && !isTerminal) {
      setIsStreaming(true)
      
      const setupStream = async () => {
        const token = localStorage.getItem('codepilot_token')
        const url = `${BASE_URL}/workflows/${workflow.id}/stream`
        const controller = new AbortController()
        abortControllerRef.current = controller

        try {
          const response = await fetch(url, {
            headers: { Authorization: `Bearer ${token}` },
            signal: controller.signal
          })
          
          if (!response.ok) throw new Error('Stream failed')
          
          const reader = response.body.getReader()
          const decoder = new TextDecoder()
          let buffer = ''
          
          while (true) {
            const { value, done } = await reader.read()
            if (done) break
            buffer += decoder.decode(value, { stream: true })
            
            const lines = buffer.split('\n\n')
            buffer = lines.pop()
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6))
                
                if (data.error || data.done) {
                  setIsStreaming(false)
                  break
                }
                
                if (data.agent || data.status) {
                  setLiveLogs(prev => {
                     if (prev.some(l => l.message === data.message && l.timestamp === data.timestamp)) return prev
                     return [...prev, data]
                  })
                }
              }
            }
          }
        } catch (err) {
          if (err.name !== 'AbortError') console.error('SSE Error:', err)
          setIsStreaming(false)
        }
      }
      
      setupStream()
      
      return () => {
        if (abortControllerRef.current) abortControllerRef.current.abort()
      }
    } else {
      setLiveLogs(result.logs || [])
      setIsStreaming(false)
    }
  }, [expanded, workflow.id, statusKey])

  let currentAgent = ''
  let thinking = ''
  let completedSteps = result.completed_steps ? [...result.completed_steps] : []
  
  const lastSupervisorLog = [...liveLogs].reverse().find(l => l.agent === 'supervisor' && l.status === 'routed')
  if (lastSupervisorLog) {
      const match = lastSupervisorLog.message.match(/Routing to (\w+): (.*)/)
      if (match) {
          currentAgent = match[1]
          thinking = match[2]
      }
  }

  if (['completed', 'failed', 'rejected', 'waiting_for_approval', 'awaiting_approval'].includes(statusKey)) {
      currentAgent = ''
      thinking = ''
  }


  liveLogs.forEach(log => {
      if (log.status === 'completed' && log.agent !== 'supervisor' && log.agent !== 'human_approval' && !completedSteps.includes(log.agent)) {
          completedSteps.push(log.agent)
      }
  })

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
          
          {currentAgent && (
            <div className="active-agent-banner card" style={{ padding: '0.75rem 1rem', marginBottom: '1rem', background: 'var(--surface-color)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div className="node-pulse" style={{ width: 12, height: 12, backgroundColor: 'var(--primary-color)', flexShrink: 0 }}></div>
              <div style={{ flex: 1 }}>
                <strong style={{ textTransform: 'capitalize' }}>{currentAgent}</strong> is working...
                {thinking && <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>💬 "{thinking}"</div>}
              </div>
            </div>
          )}

          <WorkflowPipeline
            completedSteps={completedSteps}
            currentAgent={currentAgent}
            errors={result.errors || []}
          />

          {liveLogs.length > 0 && <StreamingLog logs={liveLogs} isStreaming={isStreaming} title="Execution Log" />}

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

          {/* Generated Code Review */}
          {workflow.status === 'awaiting_approval' && (
            <div className="wf-plan-box" style={{ marginTop: '1.5rem' }}>
              <h4>Review Generated Code</h4>
              <p className="text-muted">Review the files created or modified by the agents below:</p>
              
              <div className="generated-files-list">
                {/* CodeGen Files */}
                {result.codegen_result?.files?.map((f, i) => (
                  <details key={`codegen-${i}`} className="gf-content-details card" style={{ padding: '0.5rem 1rem', marginTop: '0.5rem' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 500 }}>
                      <span className={`badge badge-${f.action === 'delete' ? 'error' : f.action === 'modify' ? 'warning' : 'success'}`} style={{ marginRight: '0.5rem' }}>
                        {f.action}
                      </span>
                      {f.path}
                    </summary>
                    {f.description && <p className="text-muted" style={{ margin: '0.5rem 0 0.5rem 0', fontSize: '0.875rem' }}>{f.description}</p>}
                    <pre className="code-block" style={{ maxHeight: '300px', overflowY: 'auto' }}>{f.content}</pre>
                  </details>
                ))}

                {/* Refactor Files */}
                {result.refactor_result?.refactored_files?.map((f, i) => (
                  <details key={`refactor-${i}`} className="gf-content-details card" style={{ padding: '0.5rem 1rem', marginTop: '0.5rem' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 500 }}>
                      <span className="badge badge-warning" style={{ marginRight: '0.5rem' }}>refactor</span>
                      {f.path}
                    </summary>
                    <pre className="code-block" style={{ maxHeight: '300px', overflowY: 'auto', marginTop: '0.5rem' }}>{f.refactored_content}</pre>
                  </details>
                ))}

                {/* Testing Files */}
                {result.testing_result?.test_files?.map((f, i) => (
                  <details key={`test-${i}`} className="gf-content-details card" style={{ padding: '0.5rem 1rem', marginTop: '0.5rem' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 500 }}>
                      <span className="badge badge-info" style={{ marginRight: '0.5rem' }}>test</span>
                      {f.path}
                    </summary>
                    <pre className="code-block" style={{ maxHeight: '300px', overflowY: 'auto', marginTop: '0.5rem' }}>{f.content}</pre>
                  </details>
                ))}
              </div>
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

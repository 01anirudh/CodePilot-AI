import './WorkflowPipeline.css'

const AGENTS = [
  { id: 'analyzer',  label: 'Analyzer',  icon: '🔍', color: '#6366f1' },
  { id: 'knowledge', label: 'Knowledge', icon: '🧠', color: '#8b5cf6' },
  { id: 'planner',   label: 'Planner',   icon: '📋', color: '#06b6d4' },
  { id: 'codegen',   label: 'CodeGen',   icon: '⚡', color: '#f59e0b' },
  { id: 'refactor',  label: 'Refactor',  icon: '🔧', color: '#10b981' },
  { id: 'testing',   label: 'Testing',   icon: '🧪', color: '#3b82f6' },
  { id: 'reviewer',  label: 'Review',    icon: '👁️', color: '#ef4444' },
  { id: 'docs',      label: 'Docs',      icon: '📚', color: '#84cc16' },
  { id: 'github',    label: 'GitHub',    icon: '🐙', color: '#f97316' },
]

const STATUS_STATES = {
  completed: 'node-completed',
  running: 'node-running',
  pending: 'node-pending',
  failed: 'node-failed',
  skipped: 'node-skipped',
}

export default function WorkflowPipeline({ completedSteps = [], currentAgent = '', errors = [] }) {
  const errorAgents = errors.map(e => e.agent)

  return (
    <div className="workflow-pipeline">
      {AGENTS.map((agent, i) => {
        const isDone = completedSteps.includes(agent.id)
        const isRunning = currentAgent === agent.id
        const hasError = errorAgents.includes(agent.id)
        const statusClass = hasError ? 'node-failed' : isDone ? 'node-completed' : isRunning ? 'node-running' : 'node-pending'

        return (
          <div key={agent.id} className="pipeline-step">
            <div
              className={`pipeline-node ${statusClass}`}
              style={{ '--node-color': agent.color }}
              title={agent.label}
            >
              <span className="node-icon">{agent.icon}</span>
              {isRunning && <div className="node-pulse" />}
              {isDone && !hasError && (
                <div className="node-check">✓</div>
              )}
              {hasError && (
                <div className="node-error-badge">✕</div>
              )}
            </div>
            <span className="node-label">{agent.label}</span>
            {i < AGENTS.length - 1 && (
              <div className={`pipeline-connector ${isDone ? 'connector-done' : ''}`} />
            )}
          </div>
        )
      })}
    </div>
  )
}

import './AgentCard.css'

const STATUS_MAP = {
  completed: { label: 'Completed', cls: 'badge-success', dot: 'dot-success' },
  running:   { label: 'Running',   cls: 'badge-info',    dot: 'dot-info' },
  pending:   { label: 'Pending',   cls: 'badge-muted',   dot: 'dot-muted' },
  failed:    { label: 'Failed',    cls: 'badge-error',   dot: 'dot-error' },
  skipped:   { label: 'Skipped',  cls: 'badge-muted',   dot: 'dot-muted' },
  idle:      { label: 'Idle',     cls: 'badge-muted',   dot: 'dot-muted' },
}

export default function AgentCard({ agent, status = 'idle', lastRun, onClick }) {
  const s = STATUS_MAP[status] || STATUS_MAP.idle

  return (
    <div
      className="agent-card card"
      style={{ '--agent-color': agent.color }}
      onClick={onClick}
    >
      <div className="agent-card-header">
        <div className="agent-emoji" style={{ background: `${agent.color}20`, border: `1px solid ${agent.color}40` }}>
          {agent.icon}
        </div>
        <span className={`badge ${s.cls}`}>
          <span className={`dot ${s.dot}`} />
          {s.label}
        </span>
      </div>

      <h4 className="agent-name">{agent.name}</h4>
      <p className="agent-desc">{agent.description}</p>

      <div className="agent-capabilities">
        {(agent.capabilities || []).slice(0, 3).map((cap) => (
          <span key={cap} className="capability-tag">{cap}</span>
        ))}
      </div>

      {lastRun && (
        <div className="agent-meta">
          <span>Last run: {new Date(lastRun).toLocaleDateString()}</span>
        </div>
      )}

      <div className="agent-glow" />
    </div>
  )
}

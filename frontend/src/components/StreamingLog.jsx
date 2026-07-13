import { useEffect, useRef } from 'react'
import { Terminal, CheckCircle2, XCircle, Clock, Loader2 } from 'lucide-react'
import './StreamingLog.css'

const LOG_ICONS = {
  completed: <CheckCircle2 size={14} className="log-icon success" />,
  error:     <XCircle size={14} className="log-icon error" />,
  running:   <Loader2 size={14} className="log-icon spin info" />,
  waiting:   <Clock size={14} className="log-icon warn" />,
  default:   <Terminal size={14} className="log-icon muted" />,
}

const AGENT_COLORS = {
  analyzer:  '#6366f1',
  knowledge: '#8b5cf6',
  planner:   '#06b6d4',
  codegen:   '#f59e0b',
  refactor:  '#10b981',
  testing:   '#3b82f6',
  reviewer:  '#ef4444',
  docs:      '#84cc16',
  github:    '#f97316',
  human_approval: '#ec4899',
}

export default function StreamingLog({ logs = [], isStreaming = false, title = 'Agent Activity' }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  return (
    <div className="streaming-log card">
      <div className="log-header">
        <div className="log-title">
          <Terminal size={16} />
          <span>{title}</span>
          {isStreaming && (
            <span className="streaming-indicator">
              <span className="dot dot-info animate-pulse-ring" />
              Live
            </span>
          )}
        </div>
        <span className="log-count">{logs.length} events</span>
      </div>

      <div className="log-body">
        {logs.length === 0 && (
          <div className="log-empty">
            <Terminal size={32} />
            <p>Waiting for agent activity...</p>
          </div>
        )}

        {logs.map((log, i) => {
          const icon = LOG_ICONS[log.status] || LOG_ICONS.default
          const agentColor = AGENT_COLORS[log.agent] || '#a0a0c0'

          return (
            <div key={i} className={`log-entry log-${log.status || 'default'}`} style={{ '--agent-color': agentColor }}>
              <div className="log-entry-left">
                {icon}
                <span className="log-agent" style={{ color: agentColor }}>
                  [{log.agent}]
                </span>
                <span className="log-message">{log.message}</span>
              </div>
              <span className="log-time">
                {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ''}
              </span>
            </div>
          )
        })}

        {isStreaming && (
          <div className="log-entry log-streaming">
            <Loader2 size={14} className="animate-spin log-icon info" />
            <span className="log-agent" style={{ color: '#06b6d4' }}>Processing...</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}

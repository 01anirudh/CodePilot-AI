import { useEffect, useState } from 'react'
import AgentCard from '../components/AgentCard'
import useAppStore from '../stores/appStore'
import './Agents.css'

export default function Agents() {
  const { agents, agentsLoading, fetchAgents } = useAppStore()
  const [selected, setSelected] = useState(null)

  useEffect(() => { fetchAgents() }, [])

  return (
    <div className="agents-page animate-fade-up">
      <div className="page-header">
        <div>
          <h1>Agents</h1>
          <p className="text-muted">9 specialized AI agents working autonomously</p>
        </div>
        <div className="agents-summary">
          <span className="badge badge-success">
            <span className="dot dot-success" />
            All Systems Operational
          </span>
        </div>
      </div>

      {/* Architecture Flow */}
      <div className="card agent-architecture">
        <h3>Agent Orchestration Flow</h3>
        <p className="text-muted" style={{ marginBottom: '1.5rem' }}>
          LangGraph StateGraph with human-in-the-loop checkpoint
        </p>
        <div className="arch-flow">
          <div className="arch-group">
            <span className="arch-label">Input</span>
            <div className="arch-node input-node">📥 Task Request</div>
          </div>
          
          <div className="arch-arrow">→</div>
          
          <div className="arch-group" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span className="arch-label">Dynamic Router</span>
            <div className="arch-node" style={{ background: '#ec489920', borderColor: '#ec4899', padding: '1.5rem', fontWeight: 'bold', boxShadow: '0 0 15px #ec489940' }}>
              👑 Supervisor LLM
            </div>
            <span className="text-muted" style={{ fontSize: '0.75rem', marginTop: '0.5rem' }}>Decides next step</span>
          </div>

          <div className="arch-arrow">↔</div>

          <div className="arch-group">
            <span className="arch-label">Specialized Agent Pool</span>
            <div className="arch-parallel" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem', padding: '0.5rem', background: 'var(--surface-color)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              {[
                ['🔍', 'Analyzer', '#6366f1'],
                ['🧠', 'Knowledge', '#8b5cf6'],
                ['📋', 'Planner', '#06b6d4'],
                ['⚡', 'CodeGen', '#f59e0b'],
                ['🔧', 'Refactor', '#10b981'],
                ['🧪', 'Testing', '#3b82f6'],
                ['👁️', 'Review', '#ef4444'],
                ['📚', 'Docs', '#84cc16'],
              ].map(([icon, name, color]) => (
                <div key={name} className="arch-node" style={{ background: `${color}15`, borderColor: color, margin: 0, padding: '0.5rem 1rem' }}>
                  {icon} {name}
                </div>
              ))}
            </div>
          </div>

          <div className="arch-arrow">→</div>

          <div className="arch-group">
            <span className="arch-label">Gate & Output</span>
            <div className="arch-stack" style={{ gap: '0.5rem' }}>
              <div className="arch-node human-node">👤 Human Approval</div>
              <div className="arch-node" style={{ background: '#f9731620', borderColor: '#f97316' }}>🐙 GitHub PR</div>
            </div>
          </div>
        </div>
      </div>


    </div>
  )
}

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
          <div className="arch-group">
            <span className="arch-label">Analysis</span>
            <div className="arch-stack">
              <div className="arch-node" style={{ background: '#6366f120', borderColor: '#6366f1' }}>🔍 Analyzer</div>
              <div className="arch-node" style={{ background: '#8b5cf620', borderColor: '#8b5cf6' }}>🧠 Knowledge</div>
              <div className="arch-node" style={{ background: '#06b6d420', borderColor: '#06b6d4' }}>📋 Planner</div>
            </div>
          </div>
          <div className="arch-arrow">→</div>
          <div className="arch-group">
            <span className="arch-label">Execution (Parallel)</span>
            <div className="arch-parallel">
              {[
                ['⚡', 'CodeGen', '#f59e0b'],
                ['🔧', 'Refactor', '#10b981'],
                ['🧪', 'Testing', '#3b82f6'],
                ['👁️', 'Review', '#ef4444'],
                ['📚', 'Docs', '#84cc16'],
              ].map(([icon, name, color]) => (
                <div key={name} className="arch-node" style={{ background: `${color}20`, borderColor: color }}>
                  {icon} {name}
                </div>
              ))}
            </div>
          </div>
          <div className="arch-arrow">→</div>
          <div className="arch-group">
            <span className="arch-label">Gate</span>
            <div className="arch-node human-node">👤 Human Approval</div>
          </div>
          <div className="arch-arrow">→</div>
          <div className="arch-group">
            <span className="arch-label">Output</span>
            <div className="arch-node" style={{ background: '#f9731620', borderColor: '#f97316' }}>🐙 GitHub PR</div>
          </div>
        </div>
      </div>


    </div>
  )
}

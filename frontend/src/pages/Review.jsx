import { useEffect, useState } from 'react'
import { githubApi } from '../services/api'
import './Review.css'

export default function Review() {
  const [prs, setPRs] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    fetchPRs()
  }, [])

  const fetchPRs = async () => {
    setLoading(true)
    try {
      const res = await githubApi.listPRs()
      setPRs(res.data)
    } catch { } finally { setLoading(false) }
  }

  const handleApprove = async (approved) => {
    setSubmitting(true)
    try {
      await githubApi.approvePR(selected.id, approved, comment)
      await fetchPRs()
      setSelected(null)
      setComment('')
    } finally { setSubmitting(false) }
  }

  const STATUS_CONFIG = {
    draft:            { cls: 'badge-muted', label: 'Draft' },
    pending_approval: { cls: 'badge-warning', label: 'Pending Approval' },
    approved:         { cls: 'badge-success', label: 'Approved' },
    rejected:         { cls: 'badge-error', label: 'Rejected' },
    merged:           { cls: 'badge-brand', label: 'Merged' },
  }

  return (
    <div className="review-page animate-fade-up">
      <div className="page-header">
        <div>
          <h1>Review</h1>
          <p className="text-muted">Human-in-the-loop code review and PR approval</p>
        </div>
      </div>

      {loading ? (
        <div className="loading-placeholder">Loading pull requests...</div>
      ) : prs.length === 0 ? (
        <div className="empty-state card">
          <span style={{ fontSize: '3rem' }}>🐙</span>
          <h3>No pull requests yet</h3>
          <p>Pull requests created by AI agents will appear here for your review.</p>
        </div>
      ) : (
        <div className="review-layout">
          {/* PR List */}
          <div className="pr-list">
            {prs.map(pr => {
              const sc = STATUS_CONFIG[pr.status] || STATUS_CONFIG.draft
              return (
                <div
                  key={pr.id}
                  className={`card pr-card ${selected?.id === pr.id ? 'selected' : ''}`}
                  onClick={() => setSelected(pr)}
                >
                  <div className="pr-card-header">
                    <span className={`badge ${sc.cls}`}>{sc.label}</span>
                    {pr.github_pr_url && (
                      <a href={pr.github_pr_url} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm" onClick={e => e.stopPropagation()}>
                        ↗ GitHub
                      </a>
                    )}
                  </div>
                  <p className="pr-title">{pr.title}</p>
                  <p className="pr-meta">
                    {pr.branch_name} → {pr.base_branch}
                    {pr.files_changed && ` · ${Object.keys(pr.files_changed).length} files`}
                  </p>
                </div>
              )
            })}
          </div>

          {/* PR Detail */}
          {selected ? (
            <div className="pr-detail card">
              <h3>{selected.title}</h3>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem', marginTop: '0.5rem' }}>
                <span className="badge badge-muted">{selected.branch_name}</span>
                <span className="badge badge-muted">→ {selected.base_branch}</span>
              </div>

              {selected.description && (
                <div className="pr-description">
                  <h4>Description</h4>
                  <pre className="code-block">{selected.description.slice(0, 1000)}</pre>
                </div>
              )}

              {selected.files_changed && (
                <div className="files-changed">
                  <h4>Files Changed</h4>
                  {Object.entries(selected.files_changed).map(([path, action]) => (
                    <div key={path} className="file-row">
                      <span className={`file-action ${action}`}>{action}</span>
                      <span className="file-path">{path}</span>
                    </div>
                  ))}
                </div>
              )}

              {selected.status === 'pending_approval' && (
                <div className="approval-section" style={{ marginTop: '1.5rem' }}>
                  <h4>Your Review</h4>
                  <textarea
                    className="input"
                    rows={3}
                    placeholder="Add a review comment (optional)"
                    value={comment}
                    onChange={e => setComment(e.target.value)}
                    style={{ marginTop: '0.5rem', marginBottom: '1rem', resize: 'vertical' }}
                  />
                  <div className="approval-actions">
                    <button className="btn btn-danger" onClick={() => handleApprove(false)} disabled={submitting}>
                      ✕ Request Changes
                    </button>
                    <button className="btn btn-primary" onClick={() => handleApprove(true)} disabled={submitting}>
                      ✓ Approve & Merge
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="pr-detail card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              <p>Select a pull request to review</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { Plus, GitBranch, Trash2, ExternalLink, RefreshCw, Search } from 'lucide-react'
import useAppStore from '../stores/appStore'
import './Repositories.css'

const STATUS_CONFIG = {
  pending:   { cls: 'badge-muted',    label: 'Pending' },
  analyzing: { cls: 'badge-info',     label: 'Analyzing' },
  analyzed:  { cls: 'badge-success',  label: 'Analyzed' },
  error:     { cls: 'badge-error',    label: 'Error' },
}

export default function Repositories() {
  const { repositories, reposLoading, fetchRepositories, addRepository, removeRepository } = useAppStore()
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ github_url: '', name: '', description: '' })
  const [adding, setAdding] = useState(false)
  const [search, setSearch] = useState('')
  const [error, setError] = useState('')

  useEffect(() => { fetchRepositories() }, [])

  const handleAdd = async (e) => {
    e.preventDefault()
    setAdding(true)
    setError('')
    try {
      await addRepository(form)
      setForm({ github_url: '', name: '', description: '' })
      setShowAdd(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add repository')
    } finally {
      setAdding(false)
    }
  }

  const filtered = repositories.filter(r =>
    r.name?.toLowerCase().includes(search.toLowerCase()) ||
    r.github_url?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="repositories animate-fade-up">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>Repositories</h1>
          <p className="text-muted">Connect GitHub repositories for analysis and automation</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-ghost btn-icon" onClick={fetchRepositories} title="Refresh">
            <RefreshCw size={16} className={reposLoading ? 'animate-spin' : ''} />
          </button>
          <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
            <Plus size={16} /> Add Repository
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="search-bar">
        <Search size={16} className="search-icon" />
        <input
          className="input search-input"
          placeholder="Search repositories..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* Add Repo Modal */}
      {showAdd && (
        <div className="modal-overlay" onClick={() => setShowAdd(false)}>
          <div className="modal card" onClick={e => e.stopPropagation()}>
            <h3>Connect Repository</h3>
            <p className="text-muted" style={{ marginBottom: '1.5rem' }}>
              Enter a GitHub repository URL to start analysis
            </p>
            <form onSubmit={handleAdd} className="add-form">
              <div className="input-group">
                <label className="input-label">GitHub URL *</label>
                <input
                  className="input"
                  placeholder="https://github.com/owner/repo"
                  value={form.github_url}
                  onChange={e => setForm(f => ({ ...f, github_url: e.target.value }))}
                  required
                />
              </div>
              <div className="input-group">
                <label className="input-label">Display Name</label>
                <input
                  className="input"
                  placeholder="Auto-detected from URL"
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                />
              </div>
              <div className="input-group">
                <label className="input-label">Description</label>
                <input
                  className="input"
                  placeholder="Optional description"
                  value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                />
              </div>
              {error && <div className="alert alert-error">{error}</div>}
              <div className="form-actions">
                <button type="button" className="btn btn-ghost" onClick={() => setShowAdd(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={adding}>
                  {adding ? 'Connecting...' : 'Connect Repository'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Repo Grid */}
      {reposLoading ? (
        <div className="repos-loading">
          {[1, 2, 3].map(i => <div key={i} className="card repo-skeleton"><div className="skeleton-line tall" /><div className="skeleton-line short" /></div>)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state card">
          <GitBranch size={48} />
          <h3>No repositories yet</h3>
          <p>Connect a GitHub repository to start analyzing your codebase.</p>
          <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
            <Plus size={16} /> Add Repository
          </button>
        </div>
      ) : (
        <div className="repos-grid grid-3">
          {filtered.map(repo => (
            <RepoCard key={repo.id} repo={repo} onDelete={() => removeRepository(repo.id)} />
          ))}
        </div>
      )}
    </div>
  )
}

function RepoCard({ repo, onDelete }) {
  const sc = STATUS_CONFIG[repo.status] || STATUS_CONFIG.pending

  return (
    <div className="card repo-card">
      <div className="repo-header">
        <div className="repo-icon">
          <GitBranch size={20} />
        </div>
        <span className={`badge ${sc.cls}`}>{sc.label}</span>
      </div>

      <h4 className="repo-name">{repo.full_name || repo.name}</h4>
      <p className="repo-desc">{repo.description || 'No description'}</p>

      <div className="repo-tags">
        {repo.language && <span className="capability-tag">{repo.language}</span>}
        {repo.framework && <span className="capability-tag">{repo.framework}</span>}
      </div>

      {repo.analysis_result && (
        <div className="repo-analysis">
          <div className="analysis-row">
            <span>Architecture</span>
            <span>{repo.analysis_result.architecture_pattern || '—'}</span>
          </div>
          <div className="analysis-row">
            <span>Complexity</span>
            <span>{repo.analysis_result.complexity_score ?? '—'}/10</span>
          </div>
          <div className="analysis-row">
            <span>Embeddings</span>
            <span>{repo.embedding_count || 0} chunks</span>
          </div>
        </div>
      )}

      <div className="repo-actions">
        {repo.github_url && (
          <a href={repo.github_url} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm">
            <ExternalLink size={14} /> GitHub
          </a>
        )}
        <button className="btn btn-danger btn-sm btn-icon" onClick={onDelete} title="Delete">
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  )
}

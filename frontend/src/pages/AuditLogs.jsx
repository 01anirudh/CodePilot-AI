import { useEffect, useState } from 'react'
import { auditApi } from '../services/api'
import { Search, Filter } from 'lucide-react'
import './AuditLogs.css'

const ACTION_COLOR = (action) => {
  if (action.includes('created') || action.includes('registered')) return 'badge-success'
  if (action.includes('deleted') || action.includes('rejected')) return 'badge-error'
  if (action.includes('approved') || action.includes('completed')) return 'badge-brand'
  if (action.includes('login')) return 'badge-info'
  return 'badge-muted'
}

export default function AuditLogs() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [resourceType, setResourceType] = useState('')

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const res = await auditApi.list({ action: search || undefined, resource_type: resourceType || undefined, limit: 100 })
      setLogs(res.data)
    } catch { } finally { setLoading(false) }
  }

  useEffect(() => { fetchLogs() }, [])

  return (
    <div className="audit-page animate-fade-up">
      <div className="page-header">
        <div>
          <h1>Audit Logs</h1>
          <p className="text-muted">Complete audit trail of all system actions</p>
        </div>
      </div>

      {/* Filters */}
      <div className="audit-filters">
        <div className="search-bar" style={{ flex: 1 }}>
          <Search size={16} className="search-icon" />
          <input className="input search-input" placeholder="Search actions..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <select className="input" style={{ width: 200 }} value={resourceType} onChange={e => setResourceType(e.target.value)}>
          <option value="">All resources</option>
          <option value="workflow">Workflow</option>
          <option value="repository">Repository</option>
          <option value="pull_request">Pull Request</option>
          <option value="user">User</option>
          <option value="github">GitHub</option>
        </select>
        <button className="btn btn-secondary" onClick={fetchLogs}>
          <Filter size={16} /> Filter
        </button>
      </div>

      {/* Table */}
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Action</th>
              <th>Resource</th>
              <th>Resource ID</th>
              <th>IP Address</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>Loading...</td></tr>
            ) : logs.length === 0 ? (
              <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>No audit logs found</td></tr>
            ) : logs.map(log => (
              <tr key={log.id}>
                <td><span className={`badge ${ACTION_COLOR(log.action)}`}>{log.action}</span></td>
                <td>{log.resource_type || '—'}</td>
                <td style={{ fontFamily: 'monospace', fontSize: '0.75rem', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{log.resource_id || '—'}</td>
                <td>{log.ip_address || '—'}</td>
                <td style={{ whiteSpace: 'nowrap' }}>{new Date(log.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

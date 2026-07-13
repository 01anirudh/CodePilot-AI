import { useState } from 'react'
import { Save, Eye, EyeOff } from 'lucide-react'
import useAppStore from '../stores/appStore'
import './Settings.css'

const LLM_PROVIDERS = [
  { value: 'openai', label: 'OpenAI GPT-4o', desc: 'Best quality, requires API key' },
  { value: 'gemini', label: 'Google Gemini', desc: 'Fast and capable, requires API key' },
  { value: 'ollama', label: 'Ollama (Local)', desc: 'Privacy-first, runs locally, no key needed' },
]

export default function Settings() {
  const { user } = useAppStore()
  const [saved, setSaved] = useState(false)
  const [show, setShow] = useState({})
  const [form, setForm] = useState({
    llm_provider: 'openai',
    openai_api_key: '',
    gemini_api_key: '',
    ollama_url: 'http://localhost:11434',
    github_token: user?.github_token || '',
    qdrant_url: 'http://localhost:6333',
    model: 'gpt-4o',
  })

  const toggle = (key) => setShow(s => ({ ...s, [key]: !s[key] }))

  const handleSave = (e) => {
    e.preventDefault()
    // In production: call API to save settings
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="settings-page animate-fade-up">
      <div className="page-header">
        <div>
          <h1>Settings</h1>
          <p className="text-muted">Configure your CodePilot AI platform</p>
        </div>
        {saved && <span className="badge badge-success">✓ Settings saved</span>}
      </div>

      <form onSubmit={handleSave} className="settings-form">
        {/* LLM Provider */}
        <div className="settings-section card">
          <h3>🤖 LLM Provider</h3>
          <p className="text-muted">Choose the AI model that powers all 9 agents</p>
          <div className="provider-grid">
            {LLM_PROVIDERS.map(p => (
              <button
                key={p.value}
                type="button"
                className={`provider-option ${form.llm_provider === p.value ? 'selected' : ''}`}
                onClick={() => setForm(f => ({ ...f, llm_provider: p.value }))}
              >
                <span className="provider-name">{p.label}</span>
                <span className="provider-desc">{p.desc}</span>
              </button>
            ))}
          </div>

          {form.llm_provider === 'openai' && (
            <div className="settings-fields">
              <ApiKeyField label="OpenAI API Key" value={form.openai_api_key} show={show.openai}
                onChange={v => setForm(f => ({ ...f, openai_api_key: v }))} onToggle={() => toggle('openai')} />
              <div className="input-group">
                <label className="input-label">Model</label>
                <select className="input" value={form.model} onChange={e => setForm(f => ({ ...f, model: e.target.value }))}>
                  <option value="gpt-4o">GPT-4o (Recommended)</option>
                  <option value="gpt-4o-mini">GPT-4o Mini (Faster)</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                </select>
              </div>
            </div>
          )}

          {form.llm_provider === 'gemini' && (
            <div className="settings-fields">
              <ApiKeyField label="Gemini API Key" value={form.gemini_api_key} show={show.gemini}
                onChange={v => setForm(f => ({ ...f, gemini_api_key: v }))} onToggle={() => toggle('gemini')} />
            </div>
          )}

          {form.llm_provider === 'ollama' && (
            <div className="settings-fields">
              <div className="input-group">
                <label className="input-label">Ollama Base URL</label>
                <input className="input" value={form.ollama_url} onChange={e => setForm(f => ({ ...f, ollama_url: e.target.value }))} />
              </div>
              <div className="alert alert-info">
                Make sure Ollama is running locally with <code>ollama serve</code>.
                Pull a code model: <code>ollama pull codellama</code>
              </div>
            </div>
          )}
        </div>

        {/* GitHub */}
        <div className="settings-section card">
          <h3>🐙 GitHub Integration</h3>
          <p className="text-muted">Required for creating real pull requests</p>
          <div className="settings-fields">
            <ApiKeyField
              label="GitHub Personal Access Token"
              value={form.github_token}
              show={show.github}
              onChange={v => setForm(f => ({ ...f, github_token: v }))}
              onToggle={() => toggle('github')}
              placeholder="ghp_..."
            />
            <div className="alert alert-info">
              Create a token at <a href="https://github.com/settings/tokens" target="_blank" rel="noreferrer">github.com/settings/tokens</a> with <code>repo</code> and <code>pull_requests</code> scopes.
            </div>
          </div>
        </div>

        {/* Infrastructure */}
        <div className="settings-section card">
          <h3>🗄️ Infrastructure</h3>
          <p className="text-muted">Database and vector store connections</p>
          <div className="settings-fields">
            <div className="input-group">
              <label className="input-label">Qdrant URL</label>
              <input className="input" value={form.qdrant_url} onChange={e => setForm(f => ({ ...f, qdrant_url: e.target.value }))} />
            </div>
          </div>
          <div className="alert alert-info" style={{ marginTop: '1rem' }}>
            Infrastructure settings are primarily configured via <code>.env</code> file. These settings affect only your browser session.
          </div>
        </div>

        {/* User Profile */}
        <div className="settings-section card">
          <h3>👤 Profile</h3>
          <div className="settings-fields">
            <div className="input-group">
              <label className="input-label">Username</label>
              <input className="input" value={user?.username || ''} disabled />
            </div>
            <div className="input-group">
              <label className="input-label">Email</label>
              <input className="input" value={user?.email || ''} disabled />
            </div>
            <div className="input-group">
              <label className="input-label">Role</label>
              <input className="input" value={user?.role || ''} disabled />
            </div>
          </div>
        </div>

        <button type="submit" className="btn btn-primary btn-lg">
          <Save size={18} />
          Save Settings
        </button>
      </form>
    </div>
  )
}

function ApiKeyField({ label, value, show, onChange, onToggle, placeholder = '••••••••••••' }) {
  return (
    <div className="input-group">
      <label className="input-label">{label}</label>
      <div style={{ position: 'relative' }}>
        <input
          className="input"
          type={show ? 'text' : 'password'}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          style={{ paddingRight: '3rem' }}
        />
        <button
          type="button"
          className="btn btn-ghost btn-icon"
          onClick={onToggle}
          style={{ position: 'absolute', right: '0.25rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}
        >
          {show ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
    </div>
  )
}

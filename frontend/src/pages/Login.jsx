import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Zap, Eye, EyeOff, ArrowRight } from 'lucide-react'
import useAppStore from '../stores/appStore'
import './Login.css'

export default function Login() {
  const navigate = useNavigate()
  const { login, register } = useAppStore()
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [form, setForm] = useState({ email: '', password: '', username: '', full_name: '' })
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (mode === 'login') {
        await login(form.email, form.password)
        navigate('/')
      } else {
        await register({ email: form.email, password: form.password, username: form.username, full_name: form.full_name })
        setMode('login')
        setError('')
      }
    } catch (err) {
      setError(err.response?.data?.detail || (mode === 'login' ? 'Invalid email or password' : 'Registration failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      {/* Background */}
      <div className="login-bg">
        <div className="bg-orb orb-1" />
        <div className="bg-orb orb-2" />
        <div className="bg-orb orb-3" />
      </div>

      {/* Card */}
      <div className="login-card card-glass animate-fade-up">
        {/* Logo */}
        <div className="login-logo">
          <div className="logo-icon" style={{ width: 52, height: 52 }}>
            <Zap size={26} />
          </div>
          <div>
            <h1 className="gradient-text-animated">CodePilot AI</h1>
            <p>Autonomous Software Engineering Platform</p>
          </div>
        </div>

        {/* Tab */}
        <div className="login-tabs">
          <button
            className={`tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => { setMode('login'); setError('') }}
          >Sign In</button>
          <button
            className={`tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => { setMode('register'); setError('') }}
          >Create Account</button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="login-form">
          {mode === 'register' && (
            <>
              <div className="input-group">
                <label className="input-label">Full Name</label>
                <input className="input" placeholder="John Doe" value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))} />
              </div>
              <div className="input-group">
                <label className="input-label">Username *</label>
                <input className="input" placeholder="johndoe" value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} required />
              </div>
            </>
          )}

          <div className="input-group">
            <label className="input-label">Email *</label>
            <input className="input" type="email" placeholder="you@company.com" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} required />
          </div>

          <div className="input-group">
            <label className="input-label">Password *</label>
            <div style={{ position: 'relative' }}>
              <input
                className="input"
                type={showPass ? 'text' : 'password'}
                placeholder="••••••••"
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                required
                style={{ paddingRight: '3rem' }}
              />
              <button
                type="button"
                className="btn btn-ghost btn-icon"
                onClick={() => setShowPass(s => !s)}
                style={{ position: 'absolute', right: '0.25rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}
              >
                {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {error && <div className="alert alert-error">{error}</div>}

          <button type="submit" className="btn btn-primary btn-lg" disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
            {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
            {!loading && <ArrowRight size={18} />}
          </button>
        </form>

        {/* Demo hint */}
        <div className="login-demo">
          <p className="text-muted">
            {mode === 'login' ? (
              <>No account? <button className="link-btn" onClick={() => setMode('register')}>Create one</button></>
            ) : (
              <>Already have an account? <button className="link-btn" onClick={() => setMode('login')}>Sign in</button></>
            )}
          </p>
        </div>
      </div>

      {/* Feature Pills */}
      <div className="feature-pills">
        {['9 AI Agents', 'LangGraph', 'Human in Loop', 'GitHub PR', 'Vector Search', 'Streaming'].map(f => (
          <span key={f} className="feature-pill">{f}</span>
        ))}
      </div>
    </div>
  )
}

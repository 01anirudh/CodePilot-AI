import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export default function KPICard({ title, value, subtitle, trend, trendValue, icon: Icon, color = '#6366f1', loading }) {
  const trendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus
  const TrendIcon = trendIcon
  const trendColor = trend === 'up' ? '#22c55e' : trend === 'down' ? '#ef4444' : '#a0a0c0'

  return (
    <div className="card kpi-card" style={{ '--kpi-color': color }}>
      <div className="kpi-header">
        <div className="kpi-icon" style={{ background: `${color}20`, color }}>
          {Icon && <Icon size={20} />}
        </div>
        {trendValue && (
          <span className="kpi-trend" style={{ color: trendColor }}>
            <TrendIcon size={14} />
            {trendValue}
          </span>
        )}
      </div>

      {loading ? (
        <div className="kpi-skeleton">
          <div className="skeleton-line tall" />
          <div className="skeleton-line short" />
        </div>
      ) : (
        <>
          <div className="kpi-value">{value}</div>
          <div className="kpi-title">{title}</div>
          {subtitle && <div className="kpi-subtitle">{subtitle}</div>}
        </>
      )}

      <div className="kpi-glow" style={{ background: `radial-gradient(ellipse at bottom right, ${color}20, transparent)` }} />
    </div>
  )
}

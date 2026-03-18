interface KpiCardProps {
  label: string
  value: string | number
  sub?: string
  variant?: 'default' | 'danger' | 'success' | 'warning'
  delta?: number   // positive = up, negative = down, 0 = stable
  deltaLabel?: string
}

export default function KpiCard({ label, value, sub, variant = 'default', delta, deltaLabel }: KpiCardProps) {
  const cardClass = variant === 'danger' ? 'kpi-card kpi-card--danger' : 'kpi-card'
  const valueClass = variant !== 'default' ? `kpi-card__value kpi-card__value--${variant}` : 'kpi-card__value'

  const deltaColor = delta == null ? '' : delta > 0 ? 'var(--color-text-danger)' : delta < 0 ? 'var(--color-text-success)' : 'var(--color-text-tertiary)'
  const deltaArrow = delta == null ? '' : delta > 0 ? '↑' : delta < 0 ? '↓' : '→'

  return (
    <div className={cardClass}>
      <div className="kpi-card__label">{label}</div>
      <div className={valueClass}>{value}</div>
      {delta != null && (
        <div className="kpi-card__sub" style={{ color: deltaColor, marginTop: 6, fontWeight: 500 }}>
          {deltaArrow} {deltaLabel ?? (Math.abs(delta) + '%')}
        </div>
      )}
      {delta == null && sub && <div className="kpi-card__sub">{sub}</div>}
    </div>
  )
}

import { apiUrl } from '../../api/client'
import { useQuery } from '@tanstack/react-query'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

interface CrisisDay {
  date: string
  volume: number
  negative: number
  neg_pct: number
  is_spike: boolean
}

interface CrisisData {
  timeline: CrisisDay[]
  trend: { date: string; rolling_avg: number }[]
  peak_day: CrisisDay | null
  avg_daily_volume: number
  severity: string
  is_escalating: boolean
  warnings: string[]
  total_mentions: number
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'var(--color-text-danger)',
  high: 'var(--color-text-warning)',
  medium: 'var(--color-text-info)',
  low: 'var(--color-text-success)',
}

const SEVERITY_LABELS: Record<string, string> = {
  critical: 'CRITIQUE',
  high: 'ÉLEVÉ',
  medium: 'MOYEN',
  low: 'FAIBLE',
}

export default function CrisisPanel() {
  const { data, isLoading, error } = useQuery<CrisisData>({
    queryKey: ['crisis'],
    queryFn: () => fetch(apiUrl('/api/crisis')).then(r => r.json()),
  })

  if (isLoading) return <div className="loading">Analyse de crise en cours...</div>
  if (error) return <div className="error-msg">Erreur : {(error as Error).message}</div>
  if (!data) return null

  const severityColor = SEVERITY_COLORS[data.severity] || 'var(--color-text-tertiary)'

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">Détection de Crise — Vélo Défectueux</h2>
        <p className="section-subtitle">Analyse temps réel du volume de mentions et de la propagation</p>
      </div>

      {/* Severity banner */}
      <div className="crisis-banner" style={{ borderColor: severityColor }}>
        <div className="crisis-banner__severity" style={{ color: severityColor }}>
          {SEVERITY_LABELS[data.severity] || data.severity}
        </div>
        <div className="crisis-banner__stats">
          <span>{data.total_mentions} mentions totales</span>
          <span>Moyenne : {data.avg_daily_volume}/jour</span>
          {data.peak_day && <span>Pic : {data.peak_day.date} ({data.peak_day.volume} mentions)</span>}
          {data.is_escalating && <span className="crisis-banner__escalating">EN HAUSSE</span>}
        </div>
      </div>

      {/* Warnings */}
      {data.warnings.length > 0 && (
        <div className="crisis-warnings">
          {data.warnings.map((w, i) => (
            <div key={i} className="crisis-warning">{w}</div>
          ))}
        </div>
      )}

      {/* KPI cards */}
      <div className="kpi-row" style={{ marginBottom: 24 }}>
        <div className="kpi-card">
          <div className="kpi-card__value">{data.total_mentions}</div>
          <div className="kpi-card__label">Mentions totales</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card__value">{data.avg_daily_volume}</div>
          <div className="kpi-card__label">Moyenne/jour</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card__value">{data.peak_day?.volume || 0}</div>
          <div className="kpi-card__label">Pic journalier</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card__value">{data.total_days}</div>
          <div className="kpi-card__label">Jours de crise</div>
        </div>
      </div>

      {/* Timeline chart */}
      <div className="card" style={{ padding: 20 }}>
        <h3 style={{ fontSize: 14, marginBottom: 16, color: 'var(--color-text-secondary)' }}>
          Volume journalier de mentions
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data.timeline}>
            <defs>
              <linearGradient id="crisisGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#fc8181" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#fc8181" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-tertiary)" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--color-text-tertiary)' }} />
            <YAxis tick={{ fontSize: 10, fill: 'var(--color-text-tertiary)' }} />
            <Tooltip
              contentStyle={{ background: 'var(--color-background-secondary)', border: '1px solid var(--color-border-tertiary)', borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: 'var(--color-text-primary)' }}
            />
            <ReferenceLine y={data.avg_daily_volume * 2} stroke="var(--color-text-warning)" strokeDasharray="5 5" label={{ value: 'Seuil spike (2x)', fill: 'var(--color-text-warning)', fontSize: 10 }} />
            <Area type="monotone" dataKey="volume" stroke="#fc8181" fill="url(#crisisGrad)" strokeWidth={2} />
            <Area type="monotone" dataKey="negative" stroke="#e53e3e" fill="none" strokeWidth={1} strokeDasharray="3 3" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

import { useReputation } from '../../api/client'
import { useQuery } from '@tanstack/react-query'
import AlertBanner from '../AlertBanner'
import KpiCard from '../KpiCard'
import { AreaChart } from '@tremor/react'

interface CrisisData {
  timeline: { date: string; volume: number; negative: number; neg_pct: number; is_spike: boolean }[]
  peak_day: { date: string; volume: number } | null
  avg_daily_volume: number
  severity: string
  is_escalating: boolean
  warnings: string[]
}

export default function ReputationPanel() {
  const { data, isLoading, error } = useReputation()
  const { data: crisis } = useQuery<CrisisData>({ queryKey: ['crisis'], queryFn: () => fetch('/api/crisis').then(r => r.json()) })

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur de chargement.</div>

  const { kpis, alert, volume_by_day } = data

  // Delta 7j
  const last7 = volume_by_day.slice(-7).reduce((s, d) => s + d.volume, 0)
  const prev7 = volume_by_day.slice(-14, -7).reduce((s, d) => s + d.volume, 0)
  const volumeDelta = prev7 > 0 ? Math.round((last7 - prev7) / prev7 * 100) : null

  // Timeline data (14 derniers jours)
  const timelineData = (crisis?.timeline || volume_by_day).slice(-14).map(d => ({
    ...d,
    date: d.date.slice(5),
    negative: 'negative' in d ? d.negative : 0,
  }))

  return (
    <div>
      {/* Alert — le plus important */}
      {alert.active && <AlertBanner message={alert.message} gravityScore={alert.gravity_score} />}

      {/* 4 KPIs */}
      <div className="grid grid-cols-4 gap-3 mb-5">
        <KpiCard
          label="Gravity Score"
          value={`${kpis.gravity_score}/10`}
          variant={kpis.gravity_score > 6 ? 'danger' : kpis.gravity_score > 3 ? 'warning' : 'success'}
          sub={kpis.gravity_score > 6 ? 'Action immédiate requise' : 'Sous contrôle'}
        />
        <KpiCard
          label="Volume mentions"
          value={kpis.volume_total.toLocaleString('fr-FR')}
          delta={volumeDelta}
          deltaLabel={volumeDelta !== null ? `${volumeDelta > 0 ? '+' : ''}${volumeDelta}% vs 7j` : undefined}
        />
        <KpiCard
          label="Sentiment négatif"
          value={`${Math.round(kpis.sentiment_negatif_pct * 100)}%`}
          variant={kpis.sentiment_negatif_pct > 0.4 ? 'danger' : kpis.sentiment_negatif_pct > 0.25 ? 'warning' : 'success'}
          sub={`${Math.round(kpis.sentiment_negatif_pct * kpis.volume_total)} mentions`}
        />
        <KpiCard
          label="Détracteurs identifiés"
          value={kpis.influenceurs_detracteurs}
          sub="comptes à fort reach"
        />
      </div>

      {/* 1 seul graph — Volume + Négatif 14j */}
      <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-5 mb-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">Volume & sentiment négatif — 14 derniers jours</h3>
          {crisis?.is_escalating && (
            <span className="text-[10px] font-bold text-red-500 bg-red-50 px-2 py-0.5 rounded-full">EN HAUSSE</span>
          )}
        </div>
        <AreaChart
          data={timelineData}
          index="date"
          categories={['volume', 'negative']}
          colors={['blue', 'red']}
          showLegend={true}
          showGradient={true}
          showAnimation={true}
          curveType="monotone"
          className="h-40"
          yAxisWidth={35}
        />
      </div>

      {/* 1 reco COMEX */}
      <div className="bg-red-50 border-l-4 border-red-500 rounded-r-xl px-5 py-4">
        <div className="text-xs font-bold text-red-600 uppercase tracking-wide mb-1">Recommandation critique</div>
        <p className="text-sm text-gray-700">
          <strong>Communiqué de crise vélo — 48h max.</strong> {kpis.volume_total.toLocaleString('fr-FR')} mentions dont {Math.round(kpis.sentiment_negatif_pct * 100)}% négatives.
          Publier un communiqué transparent + hotline dédiée. Impact estimé : <strong>-60% volume négatif en 7 jours.</strong>
        </p>
      </div>
    </div>
  )
}

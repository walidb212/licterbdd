import { useReputation } from '../../api/client'
import { useQuery } from '@tanstack/react-query'
import AlertBanner from '../AlertBanner'
import KpiCard from '../KpiCard'
import CrisisLineChart from '../../charts/CrisisLineChart'
import PlatformPieChart from '../../charts/PlatformPieChart'
import { AreaChart } from '@tremor/react'

interface CrisisData {
  timeline: { date: string; volume: number; negative: number; neg_pct: number; is_spike: boolean }[]
  peak_day: { date: string; volume: number } | null
  avg_daily_volume: number
  severity: string
  is_escalating: boolean
  warnings: string[]
}

const SEV_LABELS: Record<string, string> = { critical: 'CRITIQUE', high: 'ÉLEVÉ', medium: 'MOYEN', low: 'FAIBLE' }
const SEV_COLORS: Record<string, string> = { critical: 'text-red-500 border-red-300 bg-red-50', high: 'text-amber-500 border-amber-300 bg-amber-50', medium: 'text-blue-500 border-blue-300 bg-blue-50', low: 'text-green-500 border-green-300 bg-green-50' }

export default function ReputationPanel() {
  const { data, isLoading, error } = useReputation()
  const { data: crisis } = useQuery<CrisisData>({ queryKey: ['crisis'], queryFn: () => fetch('/api/crisis').then(r => r.json()) })

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur de chargement.</div>

  const { kpis, alert, volume_by_day, platform_breakdown, top_items } = data
  const last7 = volume_by_day.slice(-7).reduce((s, d) => s + d.volume, 0)
  const prev7 = volume_by_day.slice(-14, -7).reduce((s, d) => s + d.volume, 0)
  const volumeDelta = prev7 > 0 ? Math.round((last7 - prev7) / prev7 * 100) : null

  return (
    <div>
      {alert.active && <AlertBanner message={alert.message} gravityScore={alert.gravity_score} />}

      {crisis && crisis.severity !== 'low' && (
        <div className={`flex items-center gap-4 px-4 py-2.5 rounded-xl border mb-3 text-sm ${SEV_COLORS[crisis.severity] || ''}`}>
          <span className="font-extrabold tracking-wide">{SEV_LABELS[crisis.severity]}</span>
          <div className="flex flex-wrap gap-3 text-[11px] text-gray-500">
            <span>{crisis.avg_daily_volume}/j moy.</span>
            {crisis.peak_day && <span>Pic {crisis.peak_day.date} ({crisis.peak_day.volume})</span>}
            {crisis.is_escalating && <span className="bg-red-100 text-red-600 px-1.5 py-0.5 rounded font-bold text-[9px]">EN HAUSSE</span>}
          </div>
        </div>
      )}

      {crisis?.warnings?.map((w, i) => (
        <div key={i} className="bg-amber-50/60 border-l-2 border-amber-400 px-3 py-1.5 text-[11px] text-amber-600 mb-1.5 rounded-r-md">{w}</div>
      ))}

      <div className="grid grid-cols-4 gap-3 mb-4">
        <KpiCard label="Volume mentions" value={kpis.volume_total.toLocaleString('fr-FR')} delta={volumeDelta ?? undefined}
          deltaLabel={volumeDelta != null ? `${volumeDelta > 0 ? '+' : ''}${volumeDelta}% vs 7j` : undefined}
          sub={volumeDelta == null ? 'toutes plateformes' : undefined} />
        <KpiCard label="Sentiment négatif" value={`${Math.round(kpis.sentiment_negatif_pct * 100)}%`}
          variant={kpis.sentiment_negatif_pct > 0.7 ? 'danger' : 'default'} />
        <KpiCard label="Gravity Score" value={kpis.gravity_score} sub="/ 10"
          variant={kpis.gravity_score > 6 ? 'danger' : kpis.gravity_score > 3 ? 'warning' : 'default'} />
        <KpiCard label="Influenceurs détracteurs" value={kpis.influenceurs_detracteurs} sub="comptes vérifiés" />
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        {/* Volume / jour — 2 cols */}
        <div className="col-span-2 bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-5">
          <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide mb-3">Volume / jour</h3>
          <CrisisLineChart data={volume_by_day} />
        </div>
        {/* Plateforme — 1 col */}
        <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-5">
          <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide mb-3">Plateformes</h3>
          <PlatformPieChart data={platform_breakdown} />
        </div>
      </div>

      {/* Crisis timeline — compact, only last 30 days */}
      {crisis?.timeline && crisis.timeline.length > 0 && (
        <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-5 mb-4">
          <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide mb-3">Timeline crise — Volume & Négatif</h3>
          <AreaChart
            data={crisis.timeline.slice(-30).map(d => ({ ...d, date: d.date.slice(5) }))}
            index="date"
            categories={['volume', 'negative']}
            colors={['rose', 'red']}
            showLegend={true}
            showGradient={true}
            showAnimation={true}
            curveType="monotone"
            className="h-44"
            yAxisWidth={35}
          />
        </div>
      )}

      {top_items.length > 0 && (
        <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">Top signaux prioritaires</h3>
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-gray-50">
                <th className="text-left px-3 py-2.5 text-gray-500 font-medium">Entité / Signal</th>
                <th className="text-left px-3 py-2.5 text-gray-500 font-medium">Source</th>
                <th className="text-left px-3 py-2.5 text-gray-500 font-medium">Reach</th>
                <th className="text-left px-3 py-2.5 text-gray-500 font-medium">Sentiment</th>
                <th className="text-left px-3 py-2.5 text-gray-500 font-medium">Score</th>
              </tr>
            </thead>
            <tbody>
              {top_items.map((item, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50/60 transition-colors">
                  <td className="px-3 py-2.5 max-w-[360px]">
                    {item.url
                      ? <a href={item.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-blue-600 no-underline hover:text-blue-800">{item.entity} ↗</a>
                      : <span className="font-semibold">{item.entity}</span>}
                    {item.summary && <div className="text-gray-400 mt-0.5">{item.summary.length > 100 ? item.summary.slice(0, 100) + '…' : item.summary}</div>}
                    {item.evidence?.map((e, j) => <div key={j} className="italic text-[10px] text-gray-300 mt-0.5">« {e} »</div>)}
                  </td>
                  <td className="px-3 py-2.5 text-gray-400 whitespace-nowrap">{item.source}</td>
                  <td className="px-3 py-2.5 text-gray-400 whitespace-nowrap text-[11px]">{item.followers ? item.followers.toLocaleString('fr-FR') : '—'}</td>
                  <td className="px-3 py-2.5">
                    <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold
                      ${item.sentiment === 'negative' ? 'bg-red-50 text-red-500' : item.sentiment === 'positive' ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
                      {item.sentiment}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-amber-500 font-bold">{item.priority}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

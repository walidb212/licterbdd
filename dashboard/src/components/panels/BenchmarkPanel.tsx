import { useBenchmark } from '../../api/client'
import KpiCard from '../KpiCard'
import SovBarChart from '../../charts/SovBarChart'
import SentimentRadar from '../../charts/SentimentRadar'

export default function BenchmarkPanel() {
  const { data, isLoading, error } = useBenchmark()

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur de chargement.</div>

  const { kpis, radar, sov_by_month, brand_scores } = data

  return (
    <div>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="SoV — Decathlon" value={`${Math.round(kpis.share_of_voice_decathlon * 100)}%`}
          sub={`${kpis.total_mentions} mentions`} variant={kpis.share_of_voice_decathlon > 0.5 ? 'success' : 'default'} />
        <KpiCard label="SoV — Intersport" value={`${Math.round(kpis.share_of_voice_intersport * 100)}%`} />
        <KpiCard label="Sentiment + Decathlon" value={`${Math.round(kpis.sentiment_decathlon_positive_pct * 100)}%`} variant="success" />
        <KpiCard label="Sentiment + Intersport" value={`${Math.round(kpis.sentiment_intersport_positive_pct * 100)}%`} />
      </div>

      {/* Brand score cards */}
      <div className="grid grid-cols-2 gap-5 mb-5">
        {(['decathlon', 'intersport'] as const).map(brand => {
          const s = brand_scores[brand]
          const color = brand === 'decathlon' ? 'text-[#0077c8]' : 'text-[#e8001c]'
          return (
            <div key={brand} className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
              <div className={`text-[15px] font-bold mb-1 ${color}`}>
                <a href={brand === 'decathlon' ? 'https://www.decathlon.fr' : 'https://www.intersport.fr'}
                  target="_blank" rel="noopener noreferrer" className="no-underline hover:underline" style={{ color: 'inherit' }}>
                  {brand.charAt(0).toUpperCase() + brand.slice(1)} ↗
                </a>
              </div>
              <div className="text-[11px] text-gray-400 mb-4">{s.total_mentions} mentions analysées</div>
              {[
                { label: 'Positif', pct: s.positive_pct, color: 'bg-green-500' },
                { label: 'Neutre', pct: s.neutral_pct, color: 'bg-gray-300' },
                { label: 'Négatif', pct: s.negative_pct, color: 'bg-red-400' },
              ].map(row => (
                <div key={row.label} className="flex items-center gap-2.5 mb-2">
                  <span className="w-[65px] text-[11px] text-gray-500 shrink-0">{row.label}</span>
                  <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-500 ${row.color}`} style={{ width: `${row.pct}%` }} />
                  </div>
                  <span className="w-8 text-[11px] text-gray-400 text-right">{row.pct}%</span>
                </div>
              ))}
            </div>
          )
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-5">
        <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">Share of Voice mensuel</h3>
          <SovBarChart data={sov_by_month} />
        </div>
        <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">Radar forces / faiblesses</h3>
          <SentimentRadar data={radar} />
        </div>
      </div>
    </div>
  )
}

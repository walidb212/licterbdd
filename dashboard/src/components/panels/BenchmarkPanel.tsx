import { useBenchmark } from '../../api/client'
import KpiCard from '../KpiCard'
import SentimentRadar from '../../charts/SentimentRadar'

export default function BenchmarkPanel() {
  const { data, isLoading, error } = useBenchmark()

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur de chargement.</div>

  const { kpis, radar, brand_scores } = data

  return (
    <div>
      {/* 3 KPIs */}
      <div className="grid grid-cols-3 gap-3 mb-5">
        <KpiCard label="SoV — Decathlon" value={`${Math.round(kpis.share_of_voice_decathlon * 100)}%`}
          variant="decathlon" sub={`sur ${kpis.total_mentions} mentions`} />
        <KpiCard label="SoV — Intersport" value={`${Math.round(kpis.share_of_voice_intersport * 100)}%`}
          variant={kpis.share_of_voice_intersport > kpis.share_of_voice_decathlon ? 'danger' : 'default'} />
        <KpiCard label="Mentions totales" value={kpis.total_mentions.toLocaleString('fr-FR')}
          sub="sur 12 mois" />
      </div>

      {/* Comparatif côte à côte */}
      <div className="grid grid-cols-2 gap-5 mb-5">
        {(['decathlon', 'intersport'] as const).map(brand => {
          const s = brand_scores[brand]
          const isDecathlon = brand === 'decathlon'
          const accent = isDecathlon ? '#324DE6' : '#e8001c'
          const bars = [
            { label: 'Positif', pct: s.positive_pct, bg: 'bg-green-500' },
            { label: 'Neutre', pct: s.neutral_pct, bg: 'bg-gray-300' },
            { label: 'Négatif', pct: s.negative_pct, bg: 'bg-red-400' },
          ]
          return (
            <div key={brand} className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="text-[15px] font-bold" style={{ color: accent }}>
                  {brand.charAt(0).toUpperCase() + brand.slice(1)}
                </div>
                <span className="text-[11px] text-gray-400">{s.total_mentions} mentions</span>
              </div>
              {bars.map(b => (
                <div key={b.label} className="flex items-center gap-2 mb-2.5">
                  <span className="w-14 text-[11px] text-gray-500">{b.label}</span>
                  <div className="flex-1 h-2.5 bg-gray-100 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${b.bg}`} style={{ width: `${b.pct}%` }} />
                  </div>
                  <span className="w-10 text-[12px] font-semibold text-gray-600 text-right">{b.pct}%</span>
                </div>
              ))}
            </div>
          )
        })}
      </div>

      {/* 1 graph : Radar */}
      <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-5 mb-5">
        <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide mb-3">Forces / faiblesses par topic</h3>
        <SentimentRadar data={radar} />
      </div>

      {/* Opportunité concurrentielle */}
      {(data as any).opportunity?.active && (
        <div className="bg-green-50 border-l-4 border-green-500 rounded-r-xl px-5 py-4 mb-5">
          <div className="text-xs font-bold text-green-700 uppercase tracking-wide mb-1">🚀 {(data as any).opportunity.title}</div>
          <p className="text-sm text-gray-700 mb-2">{(data as any).opportunity.message}</p>
          <ul className="text-sm text-gray-600 list-disc list-inside">
            {((data as any).opportunity.actions || []).map((a: string, i: number) => <li key={i}>{a}</li>)}
          </ul>
        </div>
      )}

      {/* Reco COMEX */}
      <div className="bg-amber-50 border-l-4 border-amber-500 rounded-r-xl px-5 py-4">
        <div className="text-xs font-bold text-amber-600 uppercase tracking-wide mb-1">Recommandation stratégique</div>
        <p className="text-sm text-gray-700">
          <strong>Ne pas engager le combat sur les marques premium.</strong> Intersport gagne sur le maillage (935 vs 335 magasins) et les grandes marques.
          Capitaliser sur les marques propres (Quechua, Domyos, Kipsta) et l'accessibilité prix où Decathlon garde <strong>+{Math.round((kpis.share_of_voice_decathlon - kpis.share_of_voice_intersport) * 100)}% de SoV.</strong>
        </p>
      </div>
    </div>
  )
}

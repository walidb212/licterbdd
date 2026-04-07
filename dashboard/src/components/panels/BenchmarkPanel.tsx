import { useBenchmark } from '../../api/client'
import KpiCard from '../KpiCard'
import SentimentRadar from '../../charts/SentimentRadar'

const TOPIC_LABELS: Record<string, string> = {
  Prix: 'Prix / Accessibilité', Sav: 'Service après-vente', Qualite: 'Qualité perçue',
  Engagement: 'Engagement communauté', Marques_propres: 'Marques propres', Service: 'Service en magasin',
}

export default function BenchmarkPanel() {
  const { data, isLoading, error } = useBenchmark()

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur de chargement.</div>

  const { kpis, radar } = data

  // Find Intersport weaknesses (score < 30%) for opportunity block
  const intWeaknesses = (radar || [])
    .filter(r => r.intersport < 50 && r.decathlon > r.intersport)
    .sort((a, b) => (b.decathlon - b.intersport) - (a.decathlon - a.intersport))

  return (
    <div>
      {/* 3 KPIs */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="bg-white shadow-sm border border-gray-100 rounded-xl px-4 py-3">
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">SoV Decathlon</div>
          <div className="text-[28px] font-black text-[#3b82f6] leading-none">{Math.round(kpis.share_of_voice_decathlon * 100)}%</div>
          <div className="text-[10px] text-gray-500">{kpis.total_mentions.toLocaleString('fr-FR')} mentions</div>
        </div>
        <div className="bg-white shadow-sm border border-gray-100 rounded-xl px-4 py-3">
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">SoV Intersport</div>
          <div className="text-[28px] font-black text-[#e8001c] leading-none">{Math.round(kpis.share_of_voice_intersport * 100)}%</div>
        </div>
        <div className="bg-white shadow-sm border border-gray-100 rounded-xl px-4 py-3">
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Mentions totales</div>
          <div className="text-[26px] font-black text-gray-900 leading-none">{kpis.total_mentions.toLocaleString('fr-FR')}</div>
        </div>
      </div>

      {/* Main: Left (table + opportunity) | Right (radar) */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        {/* LEFT: Matrice + Opportunité */}
        <div className="flex flex-col gap-2">
          {/* Matrice forces/faiblesses */}
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-3">Matrice forces / faiblesses</h3>
            <table className="w-full text-[11px]">
              <thead>
                <tr className="text-[9px] text-gray-400 uppercase">
                  <th className="text-left pb-2">Topic</th>
                  <th className="text-right pb-2 text-[#3b82f6]">Decathlon</th>
                  <th className="text-right pb-2 text-[#e8001c]">Intersport</th>
                  <th className="text-center pb-2">Leader</th>
                </tr>
              </thead>
              <tbody>
                {(radar || []).map((r, i) => {
                  const decWins = r.decathlon > r.intersport
                  const tie = Math.abs(r.decathlon - r.intersport) < 10
                  return (
                    <tr key={i} className="border-t border-gray-50">
                      <td className="py-1.5 font-medium text-gray-700">{TOPIC_LABELS[r.topic] || r.topic}</td>
                      <td className="py-1.5 text-right font-bold" style={{ color: decWins ? '#3b82f6' : '#9ca3af' }}>{r.decathlon}%</td>
                      <td className="py-1.5 text-right font-bold" style={{ color: !decWins ? '#e8001c' : '#9ca3af' }}>{r.intersport}%</td>
                      <td className="py-1.5 text-center">
                        {tie ? <span className="text-[10px] text-amber-500">⚠️</span>
                          : decWins ? <span className="text-[10px] text-green-500">✅ Dec</span>
                          : <span className="text-[10px] text-red-500">❌ Int</span>}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Opportunité Decathlon */}
          {intWeaknesses.length > 0 && (
            <div className="bg-emerald-50 border-l-4 border-emerald-500 rounded-r-xl px-4 py-3">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[11px] font-black text-emerald-700 uppercase tracking-wider">🚀 Opportunité Decathlon</span>
                {intWeaknesses.slice(0, 3).map((w, i) => (
                  <span key={i} className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-600 font-bold">{TOPIC_LABELS[w.topic] || w.topic}</span>
                ))}
              </div>
              <p className="text-[12px] text-gray-700 leading-relaxed">
                Intersport est vulnérable sur <strong>{intWeaknesses.map(w => (TOPIC_LABELS[w.topic] || w.topic).toLowerCase()).join(', ')}</strong> ({intWeaknesses.map(w => `${w.intersport}%`).join(', ')}).
                Decathlon domine ces topics ({intWeaknesses.map(w => `${w.decathlon}%`).join(', ')}).
              </p>
              <ul className="text-[11px] text-gray-600 mt-2 space-y-1 list-disc list-inside">
                <li>Amplifier le message <strong>"Sport accessible à tous"</strong> — Decathlon leader sur le prix</li>
                <li>Campagne <strong>marques propres = qualité certifiée</strong> — contrer "grandes marques = meilleur"</li>
                <li>Profiter de la crise vélo pour montrer la qualité Decathlon sur <strong>les autres catégories</strong></li>
              </ul>
            </div>
          )}
        </div>

        {/* RIGHT: Radar */}
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-2">Radar comparatif</h3>
          <SentimentRadar data={(radar || []).map(r => ({ ...r, topic: TOPIC_LABELS[r.topic] || r.topic }))} />
        </div>
      </div>

      {/* Reco stratégique */}
      <div className="bg-amber-50 border-l-4 border-amber-500 rounded-r-xl px-4 py-2.5">
        <p className="text-[12px] text-gray-800">
          <strong className="text-amber-700">STRATÉGIE :</strong> Ne pas engager le combat sur les grandes marques. Intersport gagne sur le maillage (935 vs 335 magasins).
          Capitaliser sur les marques propres et l'accessibilité prix où Decathlon garde <strong>+{Math.round((kpis.share_of_voice_decathlon - kpis.share_of_voice_intersport) * 100)}% de SoV.</strong>
        </p>
      </div>
    </div>
  )
}

import { useCx } from '../../api/client'
import KpiCard from '../KpiCard'
import RatingLineChart from '../../charts/RatingLineChart'
import RatingDistBar from '../../charts/RatingDistBar'

export default function CxPanel() {
  const { data, isLoading, error } = useCx()

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur de chargement.</div>

  const { kpis, rating_by_month, rating_distribution, irritants, enchantements, sources } = data

  return (
    <div>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Note moyenne" value={`${kpis.avg_rating} ★`}
          sub={`${kpis.total_reviews.toLocaleString('fr-FR')} avis`}
          variant={kpis.avg_rating >= 4 ? 'success' : kpis.avg_rating < 3 ? 'danger' : 'default'} />
        <KpiCard label="NPS proxy" value={kpis.nps_proxy > 0 ? `+${kpis.nps_proxy}` : `${kpis.nps_proxy}`}
          variant={kpis.nps_proxy > 20 ? 'success' : kpis.nps_proxy < 0 ? 'danger' : 'default'} />
        <KpiCard label="Total avis" value={kpis.total_reviews.toLocaleString('fr-FR')} />
        <KpiCard label="Avis négatifs SAV" value={`${Math.round(kpis.sav_negative_pct * 100)}%`}
          variant={kpis.sav_negative_pct > 0.3 ? 'danger' : 'default'} sub="des avis négatifs" />
      </div>

      <div className="grid grid-cols-2 gap-5 mb-5">
        <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
          <h3 className="text-xs font-semibold text-[#324DE6] uppercase tracking-wide mb-4">Note moyenne / mois</h3>
          <RatingLineChart data={rating_by_month} />
        </div>
        <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
          <h3 className="text-xs font-semibold text-[#324DE6] uppercase tracking-wide mb-4">Distribution des notes</h3>
          <RatingDistBar data={rating_distribution} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-5">
        {/* Irritants */}
        <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
          <h3 className="text-xs font-semibold text-[#324DE6] uppercase tracking-wide mb-4">Top 5 irritants (avis 1-2★)</h3>
          {irritants.length === 0
            ? <p className="text-gray-400 text-xs">Aucun irritant identifié.</p>
            : irritants.map((item, i) => (
              <div key={i} className="mb-3">
                <div className="flex justify-between mb-1 text-xs">
                  <span className="text-gray-600">{item.label}</span>
                  <span className="text-gray-400">{item.pct}%</span>
                </div>
                <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-red-400 rounded-full transition-all duration-500" style={{ width: `${item.bar_pct}%` }} />
                </div>
              </div>
            ))}
        </div>

        {/* Enchantements + Sources */}
        <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
          <h3 className="text-xs font-semibold text-[#324DE6] uppercase tracking-wide mb-4">Top 3 enchantements (avis 5★)</h3>
          {enchantements.length === 0
            ? <p className="text-gray-400 text-xs">Aucun enchantement identifié.</p>
            : enchantements.map((item, i) => (
              <div key={i} className="mb-3">
                <div className="flex justify-between mb-1 text-xs">
                  <span className="text-gray-600">{item.label}</span>
                  <span className="text-gray-400">{item.pct}%</span>
                </div>
                <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full transition-all duration-500" style={{ width: `${item.bar_pct}%` }} />
                </div>
              </div>
            ))}

          {sources.length > 0 && (
            <div className="mt-6 pt-4 border-t border-gray-100">
              <h3 className="text-xs font-semibold text-[#324DE6] uppercase tracking-wide mb-3">Sources</h3>
              {sources.map((s, i) => (
                <div key={i} className="flex justify-between items-center mb-1.5 text-xs">
                  {s.url
                    ? <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 no-underline hover:text-blue-700">{s.name} ↗</a>
                    : <span className="text-gray-500">{s.name}</span>}
                  <span className="text-gray-400">{s.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

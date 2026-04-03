import { useCx } from '../../api/client'
import KpiCard from '../KpiCard'

export default function CxPanel() {
  const { data, isLoading, error } = useCx()

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur de chargement.</div>

  const { kpis, irritants, enchantements } = data

  return (
    <div>
      {/* 4 KPIs */}
      <div className="grid grid-cols-4 gap-3 mb-5">
        <KpiCard
          label="NPS Proxy"
          value={kpis.nps_proxy > 0 ? `+${kpis.nps_proxy}` : `${kpis.nps_proxy}`}
          variant={kpis.nps_proxy > 20 ? 'success' : kpis.nps_proxy < 0 ? 'danger' : 'warning'}
          sub={kpis.nps_proxy > 20 ? 'Bon niveau' : kpis.nps_proxy < 0 ? 'Critique' : 'À améliorer'}
        />
        <KpiCard
          label="Note moyenne"
          value={`${kpis.avg_rating} ★`}
          variant={kpis.avg_rating >= 4 ? 'success' : kpis.avg_rating < 3 ? 'danger' : 'warning'}
          sub={`${kpis.total_reviews.toLocaleString('fr-FR')} avis`}
        />
        <KpiCard
          label="SAV négatif"
          value={`${Math.round(kpis.sav_negative_pct * 100)}%`}
          variant={kpis.sav_negative_pct > 0.3 ? 'danger' : 'warning'}
          sub="des avis négatifs"
        />
        <KpiCard
          label="Total avis"
          value={kpis.total_reviews.toLocaleString('fr-FR')}
          sub="toutes sources"
        />
      </div>

      {/* Irritants + Enchantements côte à côte */}
      <div className="grid grid-cols-2 gap-5 mb-5">
        {/* Irritants */}
        <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-5">
          <h3 className="text-[11px] font-semibold text-red-400 uppercase tracking-wide mb-4">Top 5 irritants (avis 1-2★)</h3>
          {irritants.length === 0
            ? <p className="text-gray-400 text-xs">Données insuffisantes.</p>
            : irritants.map((item, i) => (
              <div key={i} className="mb-3.5">
                <div className="flex justify-between mb-1.5">
                  <span className="text-[12px] text-gray-700 font-medium">{item.label}</span>
                  <span className="text-[12px] text-gray-400 font-semibold">{item.count} <span className="text-[10px]">({item.pct}%)</span></span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-red-400 rounded-full transition-all duration-500" style={{ width: `${item.bar_pct}%` }} />
                </div>
              </div>
            ))}
        </div>

        {/* Enchantements */}
        <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-5">
          <h3 className="text-[11px] font-semibold text-green-500 uppercase tracking-wide mb-4">Top 3 enchantements (avis 5★)</h3>
          {enchantements.length === 0
            ? <p className="text-gray-400 text-xs">Données insuffisantes.</p>
            : enchantements.map((item, i) => (
              <div key={i} className="mb-3.5">
                <div className="flex justify-between mb-1.5">
                  <span className="text-[12px] text-gray-700 font-medium">{item.label}</span>
                  <span className="text-[12px] text-gray-400 font-semibold">{item.count} <span className="text-[10px]">({item.pct}%)</span></span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full transition-all duration-500" style={{ width: `${item.bar_pct}%` }} />
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* 1 reco COMEX */}
      <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-xl px-5 py-4">
        <div className="text-xs font-bold text-blue-600 uppercase tracking-wide mb-1">Recommandation prioritaire</div>
        <p className="text-sm text-gray-700">
          <strong>Déployer un chatbot SAV de première réponse.</strong> {Math.round(kpis.sav_negative_pct * 100)}% des avis négatifs portent sur le SAV.
          Un chatbot de triage pourrait absorber 60% des cas simples (horaires, suivi commande, retours).
          <strong> Objectif : NPS +15 pts en Q3 2026.</strong>
        </p>
      </div>
    </div>
  )
}

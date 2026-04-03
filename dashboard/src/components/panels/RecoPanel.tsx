import { useRecos } from '../../api/client'

const PRIORITY_STYLES: Record<string, string> = {
  critique: 'bg-red-50 text-red-500',
  haute: 'bg-amber-50 text-amber-600',
  moyenne: 'bg-blue-50 text-blue-500',
}

export default function RecoPanel() {
  const { data, isLoading, error } = useRecos()

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur.</div>

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-base font-semibold text-[#324DE6] mb-1">Recommandations stratégiques</h2>
        <p className="text-xs text-gray-400">Actions prioritaires pour les décideurs COMEX</p>
      </div>
      <div className="grid grid-cols-2 gap-5">
        {data.recommendations.map(r => (
          <div key={r.id} className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6 hover:shadow-[0_8px_24px_rgba(0,0,0,0.1)] transition-shadow">
            <div className="flex items-center gap-2.5 mb-3">
              <span className={`text-[10px] font-bold uppercase tracking-wide px-2.5 py-1 rounded-md ${PRIORITY_STYLES[r.priority] || 'bg-gray-100 text-gray-500'}`}>
                {r.priority}
              </span>
              <span className="text-[11px] text-gray-400 ml-auto">{r.pilier}</span>
            </div>
            <h4 className="text-sm font-semibold text-gray-900 mb-2">{r.titre}</h4>
            <p className="text-xs text-gray-500 leading-relaxed mb-3">{r.description}</p>
            <div className="text-[11px] text-gray-400 border-t border-gray-100 pt-3 space-y-1">
              <div><strong className="text-gray-500">Impact :</strong> {r.impact}</div>
              <div><strong className="text-gray-500">Effort :</strong> {r.effort}</div>
              <div><strong className="text-gray-500">KPI cible :</strong> {r.kpi_cible}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

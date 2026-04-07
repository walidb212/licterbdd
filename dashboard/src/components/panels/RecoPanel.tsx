import { useRecos } from '../../api/client'

const PRIORITY_BADGE: Record<string, string> = {
  critique: 'bg-red-600 text-white',
  haute: 'bg-orange-500 text-white',
  moyenne: 'bg-yellow-400 text-black',
}

const PRIORITY_CARD: Record<string, string> = {
  critique: 'border-l-4 border-red-600 bg-red-50/50',
  haute: 'border-l-4 border-orange-400 bg-white',
  moyenne: 'border-l-4 border-yellow-300 bg-white',
}

const PILIER_BADGE: Record<string, string> = {
  'Réputation': 'bg-blue-100 text-blue-700',
  'CX': 'bg-orange-100 text-orange-700',
  'Benchmark': 'bg-purple-100 text-purple-700',
}

export default function RecoPanel() {
  const { data, isLoading, error } = useRecos()

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur.</div>

  const recos = data.recommendations
  const isOdd = recos.length % 2 !== 0

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-base font-semibold text-[#324DE6] mb-1">Recommandations stratégiques</h2>
        <p className="text-xs text-gray-400">Actions prioritaires pour les décideurs COMEX</p>
      </div>
      <div className="grid grid-cols-2 gap-5">
        {recos.map((r, i) => {
          const prio = r.priority.toLowerCase()
          const isLast = isOdd && i === recos.length - 1
          return (
            <div key={r.id} className={`rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6 hover:shadow-[0_8px_24px_rgba(0,0,0,0.1)] transition-shadow ${PRIORITY_CARD[prio] || 'bg-white'} ${isLast ? 'col-span-2' : ''}`}>
              <div className="flex items-center gap-2.5 mb-3">
                <span className={`text-[10px] font-bold uppercase tracking-wide px-2.5 py-1 rounded-md ${PRIORITY_BADGE[prio] || 'bg-gray-100 text-gray-500'}`}>
                  {r.priority}
                </span>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ml-auto ${PILIER_BADGE[r.pilier] || 'bg-gray-100 text-gray-500'}`}>
                  {r.pilier}
                </span>
              </div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2">{r.titre}</h4>
              <p className="text-xs text-gray-500 leading-relaxed mb-3">{r.description}</p>
              <div className="text-[11px] text-gray-400 border-t border-gray-100 pt-3 space-y-1">
                <div><strong className="text-gray-500">Impact :</strong> {r.impact}</div>
                <div><strong className="text-gray-500">Effort :</strong> {r.effort}</div>
                <div><strong className="text-gray-500">KPI cible :</strong> {r.kpi_cible}</div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

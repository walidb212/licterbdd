import { useSummary } from '../../api/client'

function formatFlag(flag: string) { return flag.replace(/_/g, ' ') }

export default function SynthesePanel() {
  const { data, isLoading, error } = useSummary()

  if (isLoading) return <div className="grid grid-cols-4 gap-4">{[1,2,3,4].map(i => <div key={i} className="h-20 bg-gray-100 rounded-2xl animate-pulse" />)}</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur.</div>

  const { entities, top_risks, top_opportunities } = data

  return (
    <div>
      <div className="grid grid-cols-2 gap-5 mb-5">
        {/* Risks */}
        <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
          <h3 className="text-xs font-semibold text-[#324DE6] uppercase tracking-wide mb-4">Top Risques identifiés</h3>
          {top_risks.length === 0
            ? <p className="text-gray-400 text-xs">Aucun risque agrégé.</p>
            : top_risks.map((r, i) => (
              <div key={i} className="flex items-center gap-3 mb-2">
                <span className="bg-red-50 text-red-500 rounded-md px-2 py-0.5 text-[11px] font-bold min-w-[28px] text-center">{r.count}</span>
                <span className="text-xs text-gray-600">{formatFlag(r.flag)}</span>
              </div>
            ))}
        </div>

        {/* Opportunities */}
        <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
          <h3 className="text-xs font-semibold text-[#324DE6] uppercase tracking-wide mb-4">Top Opportunités</h3>
          {top_opportunities.length === 0
            ? <p className="text-gray-400 text-xs">Aucune opportunité agrégée.</p>
            : top_opportunities.map((o, i) => (
              <div key={i} className="flex items-center gap-3 mb-2">
                <span className="bg-green-50 text-green-600 rounded-md px-2 py-0.5 text-[11px] font-bold min-w-[28px] text-center">{o.count}</span>
                <span className="text-xs text-gray-600">{formatFlag(o.flag)}</span>
              </div>
            ))}
        </div>
      </div>

      {entities.length > 0 && (
        <div className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
          <h3 className="text-xs font-semibold text-[#324DE6] uppercase tracking-wide mb-4">Entités clés — synthèse IA ({entities.length})</h3>
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-gray-50">
                <th className="text-left px-3 py-2.5 text-gray-500 font-medium">Entité</th>
                <th className="text-left px-3 py-2.5 text-gray-500 font-medium">Source</th>
                <th className="text-center px-3 py-2.5 text-gray-500 font-medium">Vol.</th>
                <th className="text-left px-3 py-2.5 text-gray-500 font-medium">Risques</th>
                <th className="text-left px-3 py-2.5 text-gray-500 font-medium">Opportunités</th>
                <th className="text-left px-3 py-2.5 text-gray-500 font-medium">Takeaway IA</th>
              </tr>
            </thead>
            <tbody>
              {entities.map((e, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50/60 transition-colors">
                  <td className="px-3 py-2.5 font-semibold whitespace-nowrap">{e.name}</td>
                  <td className="px-3 py-2.5">
                    <span className="text-[10px] px-2 py-0.5 rounded-full border border-gray-200 text-gray-500">{e.partition}</span>
                  </td>
                  <td className="px-3 py-2.5 text-center text-gray-400">{e.volume}</td>
                  <td className="px-3 py-2.5 max-w-[180px]">
                    <div className="flex flex-wrap gap-1">{e.risks.map((r, j) => (
                      <span key={j} className="text-[10px] px-1.5 py-0.5 rounded bg-red-50 text-red-500">{formatFlag(r)}</span>
                    ))}</div>
                  </td>
                  <td className="px-3 py-2.5 max-w-[180px]">
                    <div className="flex flex-wrap gap-1">{e.opportunities.map((o, j) => (
                      <span key={j} className="text-[10px] px-1.5 py-0.5 rounded bg-green-50 text-green-600">{formatFlag(o)}</span>
                    ))}</div>
                  </td>
                  <td className="px-3 py-2.5 max-w-[300px] text-gray-500 text-[11px]">
                    {e.takeaway.length > 120 ? e.takeaway.slice(0, 120) + '…' : e.takeaway}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

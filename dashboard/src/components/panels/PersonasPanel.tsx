import { useQuery } from '@tanstack/react-query'

interface Persona {
  name: string; age: number; profile: string; motivations: string[]; frustrations: string[];
  channels: string[]; satisfaction_score: number; recommendation: string
}

function toArray(val: unknown): string[] {
  if (Array.isArray(val)) return val.map(String)
  if (typeof val === 'string') return val.split(/[,;\n]/).map(s => s.trim()).filter(Boolean)
  return []
}

export default function PersonasPanel() {
  const { data, isLoading, error } = useQuery<{ personas: Persona[] }>({
    queryKey: ['personas'], queryFn: () => fetch('/api/personas').then(r => r.json()), staleTime: 1800_000,
  })

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Génération des personas via IA...</div>
  if (error) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur : {(error as Error).message}</div>

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-base font-semibold text-[#324DE6] mb-1">Personas Consommateurs</h2>
        <p className="text-xs text-gray-400">Profils synthétiques générés par IA à partir des verbatims clients</p>
      </div>
      <div className="grid grid-cols-3 gap-5">
        {(data?.personas || []).map((p, i) => (
          <div key={i} className="bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6 hover:shadow-[0_8px_24px_rgba(0,0,0,0.1)] transition-shadow">
            {/* Header */}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-11 h-11 rounded-full bg-green-700 text-white flex items-center justify-center text-lg font-bold shrink-0">
                {(p.name || '?').charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-bold text-gray-900 truncate">{p.name}</div>
                <div className="text-[11px] text-gray-400 truncate">{p.profile}</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{p.satisfaction_score}</div>
                <div className="text-[10px] text-gray-400">/10</div>
              </div>
            </div>

            {/* Motivations */}
            <div className="mb-3">
              <div className="text-[10px] font-bold uppercase tracking-wider text-blue-500 mb-1.5">Motivations</div>
              <ul className="space-y-0.5">
                {toArray(p.motivations).map((m, j) => <li key={j} className="text-xs text-gray-600 pl-3 relative before:content-['•'] before:absolute before:left-0 before:text-gray-300">{m}</li>)}
              </ul>
            </div>

            {/* Frustrations */}
            <div className="mb-3">
              <div className="text-[10px] font-bold uppercase tracking-wider text-red-500 mb-1.5">Frustrations</div>
              <ul className="space-y-0.5">
                {toArray(p.frustrations).map((f, j) => <li key={j} className="text-xs text-gray-600 pl-3 relative before:content-['•'] before:absolute before:left-0 before:text-gray-300">{f}</li>)}
              </ul>
            </div>

            {/* Channels */}
            <div className="mb-3">
              <div className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1.5">Canaux</div>
              <div className="flex flex-wrap gap-1.5">
                {toArray(p.channels).map((c, j) => <span key={j} className="bg-gray-100 rounded-full px-2.5 py-0.5 text-[11px] text-gray-500">{c}</span>)}
              </div>
            </div>

            {/* Recommendation */}
            <div className="text-xs text-gray-500 border-t border-gray-100 pt-3 mt-3">
              <strong className="text-[#324DE6]">Reco :</strong> {p.recommendation}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

import { useQuery } from '@tanstack/react-query'
import { apiUrl } from '../../api/client'

interface SwotItem { label: string; detail: string }
interface SwotData { forces: SwotItem[]; faiblesses: SwotItem[]; opportunites: SwotItem[]; menaces: SwotItem[] }

const QUADRANTS = [
  { key: 'forces', title: 'Forces', emoji: '💪', bg: 'bg-green-50', border: 'border-green-200', title_color: 'text-green-700' },
  { key: 'faiblesses', title: 'Faiblesses', emoji: '⚠️', bg: 'bg-red-50', border: 'border-red-200', title_color: 'text-red-700' },
  { key: 'opportunites', title: 'Opportunités', emoji: '🚀', bg: 'bg-blue-50', border: 'border-blue-200', title_color: 'text-blue-700' },
  { key: 'menaces', title: 'Menaces', emoji: '🔴', bg: 'bg-amber-50', border: 'border-amber-200', title_color: 'text-amber-700' },
] as const

export default function SwotPanel() {
  const { data, isLoading } = useQuery<SwotData>({
    queryKey: ['swot'],
    queryFn: () => fetch(apiUrl('/api/swot')).then(r => r.json()),
  })

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (!data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur.</div>

  return (
    <div>
      <h2 className="text-lg font-bold text-gray-800 mb-1">SWOT Social Data</h2>
      <p className="text-[11px] text-gray-400 mb-5">Analyse SWOT automatique basée sur les données sociales collectées</p>

      <div className="grid grid-cols-2 gap-4">
        {QUADRANTS.map(q => {
          const items = data[q.key as keyof SwotData] || []
          return (
            <div key={q.key} className={`${q.bg} border ${q.border} rounded-[20px] p-5`}>
              <div className={`text-[13px] font-bold ${q.title_color} mb-3`}>{q.emoji} {q.title}</div>
              <div className="space-y-2.5">
                {items.map((item, i) => (
                  <div key={i}>
                    <div className="text-[12px] font-semibold text-gray-800">{item.label}</div>
                    <div className="text-[11px] text-gray-500">{item.detail}</div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

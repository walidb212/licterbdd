import { apiUrl } from '../../api/client'
import { useQuery } from '@tanstack/react-query'

interface CityData {
  city: string; lat: number; lng: number; avg_rating: number;
  review_count: number; color: string; label: string; stores: number; brands: string[];
}

export default function HeatmapPanel() {
  const { data, isLoading, error } = useQuery<CityData[]>({
    queryKey: ['heatmap'],
    queryFn: () => fetch(apiUrl('/api/heatmap')).then(r => r.json()),
  })

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur de chargement.</div>

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-sm">Aucune donnée géographique disponible.</p>
        <p className="text-xs mt-2">Lancez le store_monitor pour collecter les avis Google Maps par ville.</p>
      </div>
    )
  }

  const avgAll = data.length ? Math.round(data.reduce((s, c) => s + c.avg_rating, 0) / data.length * 10) / 10 : 0
  const totalReviews = data.reduce((s, c) => s + c.review_count, 0)
  const worst = data[0]
  const best = data[data.length - 1]

  return (
    <div>
      {/* KPIs */}
      <div className="grid grid-cols-4 gap-3 mb-5">
        <div className="bg-white rounded-[16px] shadow-sm px-5 py-4">
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Villes analysées</div>
          <div className="text-[26px] font-bold text-gray-800">{data.length}</div>
        </div>
        <div className="bg-white rounded-[16px] shadow-sm px-5 py-4">
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Note moyenne</div>
          <div className="text-[26px] font-bold" style={{ color: avgAll >= 4 ? '#22c55e' : avgAll >= 3 ? '#f59e0b' : '#ef4444' }}>{avgAll}/5</div>
        </div>
        <div className="bg-white rounded-[16px] shadow-sm px-5 py-4">
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Pire ville</div>
          <div className="text-[20px] font-bold text-red-500">{worst?.city}</div>
          <div className="text-[11px] text-gray-400">{worst?.avg_rating}/5</div>
        </div>
        <div className="bg-white rounded-[16px] shadow-sm px-5 py-4">
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Meilleure ville</div>
          <div className="text-[20px] font-bold text-green-500">{best?.city}</div>
          <div className="text-[11px] text-gray-400">{best?.avg_rating}/5</div>
        </div>
      </div>

      {/* City table */}
      <div className="bg-white rounded-[20px] shadow-sm p-5">
        <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide mb-4">Sentiment par ville</h3>
        <table className="w-full text-[12px]">
          <thead>
            <tr className="text-[10px] text-gray-400 uppercase tracking-wider">
              <th className="text-left py-2 px-3">Ville</th>
              <th className="text-right py-2 px-3">Note</th>
              <th className="text-right py-2 px-3">Avis</th>
              <th className="text-left py-2 px-3">Niveau</th>
              <th className="text-left py-2 px-3">Barre</th>
            </tr>
          </thead>
          <tbody>
            {data.map((c, i) => (
              <tr key={i} className="border-t border-gray-50 hover:bg-gray-50/50">
                <td className="py-2.5 px-3 font-medium text-gray-700">{c.city}</td>
                <td className="py-2.5 px-3 text-right font-bold" style={{ color: c.color }}>{c.avg_rating}</td>
                <td className="py-2.5 px-3 text-right text-gray-400">{c.review_count}</td>
                <td className="py-2.5 px-3">
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold" style={{ background: c.color + '15', color: c.color }}>{c.label}</span>
                </td>
                <td className="py-2.5 px-3 w-40">
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${c.avg_rating / 5 * 100}%`, background: c.color }} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

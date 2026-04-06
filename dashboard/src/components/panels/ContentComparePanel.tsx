import { useQuery } from '@tanstack/react-query'
import Markdown from 'react-markdown'

interface CompareData {
  analysis: string
  provider: string | null
  cached_at?: string
}

export default function ContentComparePanel() {
  const { data, isLoading, error } = useQuery<CompareData>({
    queryKey: ['content-compare'],
    queryFn: () => fetch('/api/content-compare').then(r => r.json()),
    staleTime: 3600_000, // 1h cache
  })

  if (isLoading) return (
    <div className="flex flex-col items-center justify-center h-48 text-gray-400">
      <div className="text-sm mb-2">Analyse IA en cours...</div>
      <div className="text-xs">Comparaison Decathlon vs Intersport sur Instagram, TikTok, Facebook Ads</div>
    </div>
  )
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur de chargement.</div>

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-800">Comparateur de Contenu IA</h2>
          <p className="text-[11px] text-gray-400">Analyse automatique des stratégies Instagram + TikTok + Facebook Ads</p>
        </div>
        {data.provider && (
          <span className="text-[10px] text-gray-400 bg-gray-50 px-3 py-1 rounded-full">
            via {data.provider}
          </span>
        )}
      </div>

      {/* Brands comparison header */}
      <div className="grid grid-cols-2 gap-4 mb-5">
        <div className="bg-blue-50 rounded-[16px] px-5 py-4 text-center">
          <div className="text-[20px] font-bold text-[#0077c8]">Decathlon</div>
          <div className="text-[11px] text-blue-400">595K followers IG | 50K+ pubs FB</div>
        </div>
        <div className="bg-red-50 rounded-[16px] px-5 py-4 text-center">
          <div className="text-[20px] font-bold text-[#e8001c]">Intersport</div>
          <div className="text-[11px] text-red-400">148K followers IG | 46K+ pubs FB</div>
        </div>
      </div>

      {/* AI Analysis */}
      <div className="bg-white rounded-[20px] shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-sm">🤖</span>
          <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">Analyse IA comparative</h3>
        </div>
        <div className="prose prose-sm prose-gray max-w-none [&>h3]:text-[14px] [&>h3]:font-bold [&>h3]:text-gray-800 [&>h3]:mt-4 [&>h3]:mb-2 [&>p]:text-[13px] [&>p]:text-gray-600 [&>p]:mb-3 [&>ul]:text-[13px] [&>ol]:text-[13px] [&>strong]:text-gray-800">
          <Markdown>{data.analysis}</Markdown>
        </div>
      </div>
    </div>
  )
}

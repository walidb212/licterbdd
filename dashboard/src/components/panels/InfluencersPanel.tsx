import { useQuery } from '@tanstack/react-query'

interface Influencer {
  author: string; platform: string; brand_focus: string;
  posts: number; total_engagement: number; avg_sentiment: number;
  type: string; top_post: string; influence_score: number;
  sentiment_breakdown: { positive: number; negative: number; neutral: number; mixed: number };
}

const TYPE_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  ambassadeur: { bg: 'bg-green-50', text: 'text-green-600', label: 'Ambassadeur' },
  neutre: { bg: 'bg-gray-50', text: 'text-gray-500', label: 'Neutre' },
  detracteur: { bg: 'bg-red-50', text: 'text-red-600', label: 'Détracteur' },
}

const PLATFORM_ICONS: Record<string, string> = {
  Reddit: '🔴', YouTube: '▶️', TikTok: '🎵', Instagram: '📸',
  'X/Twitter': '𝕏', Presse: '📰', Facebook: '📘', Autre: '⚙️',
}

export default function InfluencersPanel() {
  const { data, isLoading, error } = useQuery<Influencer[]>({
    queryKey: ['influencers'],
    queryFn: () => fetch('/api/influencers').then(r => r.json()),
  })

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur de chargement.</div>

  const ambassadors = data.filter(i => i.type === 'ambassadeur')
  const detractors = data.filter(i => i.type === 'detracteur')
  const neutrals = data.filter(i => i.type === 'neutre')

  return (
    <div>
      {/* KPIs */}
      <div className="grid grid-cols-4 gap-3 mb-5">
        <div className="bg-white rounded-[16px] shadow-sm px-5 py-4">
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Total influenceurs</div>
          <div className="text-[26px] font-bold text-gray-800">{data.length}</div>
        </div>
        <div className="bg-white rounded-[16px] shadow-sm px-5 py-4">
          <div className="text-[10px] font-semibold text-green-400 uppercase tracking-wider mb-1">Ambassadeurs</div>
          <div className="text-[26px] font-bold text-green-500">{ambassadors.length}</div>
        </div>
        <div className="bg-white rounded-[16px] shadow-sm px-5 py-4">
          <div className="text-[10px] font-semibold text-red-400 uppercase tracking-wider mb-1">Détracteurs</div>
          <div className="text-[26px] font-bold text-red-500">{detractors.length}</div>
        </div>
        <div className="bg-white rounded-[16px] shadow-sm px-5 py-4">
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Neutres</div>
          <div className="text-[26px] font-bold text-gray-500">{neutrals.length}</div>
        </div>
      </div>

      {/* Influencer cards */}
      <div className="bg-white rounded-[20px] shadow-sm p-5">
        <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide mb-4">Top influenceurs par impact</h3>
        <div className="space-y-3">
          {data.slice(0, 15).map((inf, i) => {
            const style = TYPE_STYLES[inf.type] || TYPE_STYLES.neutre
            const icon = PLATFORM_ICONS[inf.platform] || '⚙️'
            return (
              <div key={i} className="flex items-center gap-4 p-3 rounded-xl border border-gray-100 hover:border-gray-200 transition-all">
                <div className="text-lg">{icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[13px] font-semibold text-gray-800 truncate">{inf.author}</span>
                    <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${style.bg} ${style.text}`}>{style.label}</span>
                    <span className="text-[10px] text-gray-400">{inf.platform}</span>
                  </div>
                  <div className="text-[11px] text-gray-400 mt-0.5 truncate">{inf.top_post}</div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-[13px] font-bold text-gray-700">{inf.posts} posts</div>
                  <div className="text-[10px] text-gray-400">engagement {inf.total_engagement.toLocaleString()}</div>
                </div>
                <div className="w-16 shrink-0">
                  <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden flex">
                    <div className="h-full bg-green-500" style={{ width: `${(inf.sentiment_breakdown.positive / Math.max(inf.posts, 1)) * 100}%` }} />
                    <div className="h-full bg-gray-300" style={{ width: `${(inf.sentiment_breakdown.neutral / Math.max(inf.posts, 1)) * 100}%` }} />
                    <div className="h-full bg-red-400" style={{ width: `${(inf.sentiment_breakdown.negative / Math.max(inf.posts, 1)) * 100}%` }} />
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { useCx, apiUrl } from '../../api/client'
import { useQuery } from '@tanstack/react-query'

const PLATFORM_ICONS: Record<string, { icon: string; label: string }> = {
  reddit_post: { icon: '🔴', label: 'Reddit' },
  reddit_comment: { icon: '🔴', label: 'Reddit' },
  youtube_video: { icon: '▶️', label: 'YouTube' },
  youtube_comment: { icon: '▶️', label: 'YouTube' },
  tiktok_video: { icon: '🎵', label: 'TikTok' },
  x_post: { icon: '𝕏', label: 'X/Twitter' },
  news_article: { icon: '📰', label: 'Presse' },
  review_site: { icon: '⭐', label: 'Avis' },
  store_review: { icon: '📍', label: 'Google Maps' },
}

// Simple FR detection
function isFrench(text: string): boolean {
  const frWords = ['le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'en', 'est', 'que', 'qui', 'pour', 'pas', 'sur', 'avec', 'dans', 'plus', 'mais', 'je', 'nous', 'très', 'chez']
  const words = text.toLowerCase().split(/\s+/).slice(0, 20)
  const frCount = words.filter(w => frWords.includes(w)).length
  return frCount >= 2
}

function VerbatimCarousel() {
  const [idx, setIdx] = useState(0)
  const [paused, setPaused] = useState(false)

  const { data: socialNeg } = useQuery<{ rows: Record<string, unknown>[] }>({
    queryKey: ['verb-social-neg-dec'], queryFn: () => fetch(apiUrl('/api/admindb?table=social_enriched&sentiment=negative&brand=decathlon&limit=15')).then(r => r.json()),
  })
  const { data: reviewNeg } = useQuery<{ rows: Record<string, unknown>[] }>({
    queryKey: ['verb-review-neg-dec'], queryFn: () => fetch(apiUrl('/api/admindb?table=review_enriched&sentiment=negative&brand=decathlon&limit=10')).then(r => r.json()),
  })

  const all: any[] = [
    ...(socialNeg?.rows || []),
    ...(reviewNeg?.rows || []),
  ].filter(r => {
    const text = String(r.summary_short || r.body || r.text || '')
    return text.length > 40 && isFrench(text)
  })

  // Diversify sources
  const verbatims: any[] = []
  const seenSources = new Set()
  for (const r of all) {
    const src = String(r.entity_name || r.source_name)
    if (!seenSources.has(src)) {
      verbatims.push(r)
      seenSources.add(src)
    }
    if (verbatims.length >= 6) break
  }
  if (verbatims.length < 4) verbatims.push(...all.filter(r => !verbatims.includes(r)).slice(0, 6 - verbatims.length))

  useEffect(() => {
    if (paused || !verbatims.length) return
    const timer = setInterval(() => setIdx(i => (i + 1) % verbatims.length), 5000)
    return () => clearInterval(timer)
  }, [paused, verbatims.length])

  if (!verbatims.length) return null

  const current = verbatims[idx]
  const text = String(current?.summary_short || current?.body || current?.text || '')
  const sourceName = String(current?.source_name || '')
  const platform = PLATFORM_ICONS[sourceName] || { icon: '💬', label: sourceName }
  const rawEntity = String(current?.entity_name || '')
  // Anonymize social media usernames, keep brand names for reviews
  const isUserHandle = ['reddit_post', 'reddit_comment', 'youtube_comment', 'tiktok_video'].includes(sourceName)
  const entity = isUserHandle && rawEntity && !rawEntity.toLowerCase().includes('decathlon')
    ? `Utilisateur ${platform.label}`
    : rawEntity

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 mb-3"
      onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[10px] font-semibold text-red-400 uppercase tracking-wide">Ce que disent vos clients insatisfaits</h3>
        <div className="flex gap-1">
          {verbatims.map((_, i) => (
            <button key={i} onClick={() => setIdx(i)}
              className={`w-2 h-2 rounded-full transition-all ${i === idx ? 'bg-red-400' : 'bg-gray-200'}`} />
          ))}
        </div>
      </div>

      <div className="rounded-xl p-3 bg-red-50/60 border-l-[3px] border-red-300">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-base">{platform.icon}</span>
          <span className="text-[11px] font-bold text-gray-700">{entity || platform.label}</span>
          <span className="text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-red-100 text-red-600">
            {current?.rating ? `${current.rating}★` : 'Négatif'}
          </span>
        </div>
        <p className="text-[12px] text-gray-700 italic leading-relaxed">"{text.slice(0, 200)}{text.length > 200 ? '...' : ''}"</p>
        <div className="text-[9px] text-gray-400 mt-2">
          {platform.label} • {(String(current?.published_at || '')).slice(0, 10)}
        </div>
      </div>
    </div>
  )
}

interface TopProduct {
  titre: string
  image_url: string
  mentions: number
  categorie: string
  marque_detectee: string
  url: string
  sample_reviews?: string[]
}

function ProductCard({ p, color }: { p: TopProduct; color: 'red' | 'green' }) {
  const [open, setOpen] = useState(false)
  const hasReviews = p.sample_reviews && p.sample_reviews.length > 0
  return (
    <div className="mb-2">
      <div className={`flex items-center gap-2 cursor-pointer group ${hasReviews ? 'hover:bg-' + color + '-50/50' : ''} rounded-lg p-1 -m-1 transition-colors`}
        onClick={() => hasReviews && setOpen(!open)}>
        {p.image_url ? (
          <img src={p.image_url} alt={p.titre}
            className="w-[40px] h-[40px] rounded-lg object-cover flex-shrink-0 border border-gray-100"
            onError={(e) => { (e.target as HTMLImageElement).src = ''; (e.target as HTMLImageElement).className = 'w-[40px] h-[40px] rounded-lg flex-shrink-0 bg-gray-100 flex items-center justify-center text-[14px]' }} />
        ) : (
          <div className="w-[40px] h-[40px] rounded-lg flex-shrink-0 bg-gray-100 flex items-center justify-center text-[14px]">
            {p.categorie === 'Cyclisme' ? '🚲' : p.categorie === 'Running' ? '🏃' : p.categorie === 'Randonnee' ? '🥾' : p.categorie === 'Fitness' ? '💪' : '🏷'}
          </div>
        )}
        <div className="min-w-0 flex-1">
          <div className={`text-[11px] text-gray-700 font-medium truncate group-hover:text-${color === 'red' ? 'red' : 'emerald'}-600`}>{p.titre}</div>
          <div className="text-[9px] text-gray-400">
            <span className={`font-bold ${color === 'red' ? 'text-red-400' : 'text-emerald-500'}`}>{p.mentions}</span> mentions
            <span className="mx-1">·</span>{p.categorie}
            {hasReviews && <span className="ml-1 text-blue-400">{open ? '▲' : '▼ voir avis'}</span>}
          </div>
        </div>
        <a href={p.url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
          className="text-[9px] text-blue-400 hover:text-blue-600 shrink-0">↗</a>
      </div>
      {open && p.sample_reviews && (
        <div className={`ml-12 mt-1 space-y-1 border-l-2 ${color === 'red' ? 'border-red-200' : 'border-green-200'} pl-2`}>
          {p.sample_reviews.map((r, j) => (
            <p key={j} className="text-[10px] text-gray-500 italic leading-relaxed">"{r}"</p>
          ))}
        </div>
      )}
    </div>
  )
}

function TopProductsMentioned() {
  const { data, isLoading } = useQuery<{
    negative: TopProduct[]
    positive: TopProduct[]
    insight: string
    total_reviews_scanned: number
  }>({
    queryKey: ['cx-top-products'],
    queryFn: () => fetch(apiUrl('/api/cx/top-products')).then(r => r.json()),
  })

  if (isLoading || !data) return null
  if (!data.negative?.length && !data.positive?.length) return null

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 mb-3">
      <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-3">
        Marques les plus citees dans les avis
      </h3>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="text-[9px] font-bold text-red-400 uppercase mb-2">Avis negatifs</div>
          {data.negative.slice(0, 5).map((p, i) => <ProductCard key={i} p={p} color="red" />)}
        </div>
        <div>
          <div className="text-[9px] font-bold text-emerald-500 uppercase mb-2">Avis positifs</div>
          {data.positive.slice(0, 5).map((p, i) => <ProductCard key={i} p={p} color="green" />)}
        </div>
      </div>

      {data.insight && (
        <div className="mt-3 bg-amber-50 border-l-[3px] border-amber-400 rounded-r-lg px-3 py-2">
          <p className="text-[11px] text-gray-700">
            <span className="font-bold text-amber-600">INSIGHT :</span> {data.insight}
          </p>
        </div>
      )}

      <div className="text-[8px] text-gray-300 mt-2 text-right">
        {data.total_reviews_scanned?.toLocaleString('fr-FR')} avis analyses · {(data.negative?.length || 0) + (data.positive?.length || 0)} marques detectees
      </div>
    </div>
  )
}

export default function CxPanel() {
  const { data, isLoading, error } = useCx()

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur de chargement.</div>

  const { kpis, irritants, enchantements } = data

  return (
    <div>
      {/* 4 KPIs dark */}
      <div className="grid grid-cols-4 gap-2 mb-3">
        <div className="bg-white shadow-sm border border-gray-100 rounded-xl px-4 py-3">
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">NPS Proxy</div>
          <div className={`text-[28px] font-black leading-none ${kpis.nps_proxy > 20 ? 'text-emerald-400' : kpis.nps_proxy < 0 ? 'text-red-500' : 'text-orange-400'}`}>
            {kpis.nps_proxy > 0 ? '+' : ''}{kpis.nps_proxy}
          </div>
        </div>
        <div className="bg-white shadow-sm border border-gray-100 rounded-xl px-4 py-3">
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Note moyenne</div>
          <div className="text-[26px] font-black text-amber-400 leading-none">{kpis.avg_rating} ★</div>
        </div>
        <div className="bg-white shadow-sm border border-gray-100 rounded-xl px-4 py-3">
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">SAV dans avis négatifs</div>
          <div className="text-[26px] font-black text-red-500 leading-none">40%</div>
          <div className="text-[10px] text-gray-500">1er irritant client</div>
        </div>
        <div className="bg-white shadow-sm border border-gray-100 rounded-xl px-4 py-3">
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Total avis</div>
          <div className="text-[26px] font-black text-gray-900 leading-none">{kpis.total_reviews.toLocaleString('fr-FR')}</div>
        </div>
      </div>

      {/* Irritants + Enchantements */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-[10px] font-semibold text-red-400 uppercase tracking-wide mb-3">Top irritants (avis 1-2★)</h3>
          {irritants.slice(0, 4).map((item, i) => (
            <div key={i} className="mb-2.5">
              <div className="flex justify-between mb-1">
                <span className="text-[11px] text-gray-700 font-medium">{item.label}</span>
                <span className="text-[11px] text-gray-400 font-semibold">{item.count} <span className="text-[9px]">({item.pct}%)</span></span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-red-400 rounded-full" style={{ width: `${item.bar_pct}%` }} />
              </div>
            </div>
          ))}
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-[10px] font-semibold text-green-500 uppercase tracking-wide mb-3">Top enchantements (avis 4-5★)</h3>
          {enchantements.slice(0, 4).map((item, i) => (
            <div key={i} className="mb-2.5">
              <div className="flex justify-between mb-1">
                <span className="text-[11px] text-gray-700 font-medium">{item.label}</span>
                <span className="text-[11px] text-gray-400 font-semibold">{item.count} <span className="text-[9px]">({item.pct}%)</span></span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-green-500 rounded-full" style={{ width: `${item.bar_pct}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Verbatim carousel — negative Decathlon only */}
      <VerbatimCarousel />

      {/* Top produits mentionnes dans les avis */}
      <TopProductsMentioned />

      {/* Parcours client */}
      {(data as any).parcours_client && (
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 mb-3">
          <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-3">Parcours client — Points de friction</h3>
          <div className="flex items-center justify-between gap-1.5">
            {((data as any).parcours_client || []).map((e: {etape: string; note: number; emoji: string}, i: number) => {
              const color = e.note >= 3.5 ? '#22c55e' : e.note >= 3 ? '#f59e0b' : '#ef4444'
              const bg = e.note >= 3.5 ? 'bg-green-50' : e.note >= 3 ? 'bg-amber-50' : 'bg-red-50'
              return (
                <div key={i} className="flex-1 text-center">
                  <div className={`${bg} rounded-lg p-2 mb-1`}>
                    <div className="text-sm mb-0.5">{e.emoji}</div>
                    <div className="text-[16px] font-bold" style={{ color }}>{e.note}★</div>
                  </div>
                  <div className="text-[9px] text-gray-500 font-medium">{e.etape}</div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Reco */}
      <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-xl px-4 py-2.5">
        <p className="text-[12px] text-gray-800">
          <strong className="text-blue-600">PRIORITAIRE :</strong> Chatbot SAV première réponse. 40% des avis négatifs = SAV.
          <span className="text-emerald-600 font-bold ml-1">Objectif : NPS +15 pts Q3 2026.</span>
        </p>
      </div>
    </div>
  )
}

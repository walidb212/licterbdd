import { useState, useEffect } from 'react'
import { useCx, apiUrl } from '../../api/client'
import { useQuery } from '@tanstack/react-query'

const IRRITANT_RENAME: Record<string, string> = {
  'Rapport qualité/prix': 'Qualité insuffisante vs prix',
  'Attente en caisse': 'Files d\'attente',
}
const ENCHANT_RENAME: Record<string, string> = {
  'Rapport qualité/prix': 'Excellent rapport qualité/prix',
  'Attente en caisse': 'Rapidité en magasin',
  'choix en rayon': 'Large choix produits',
}

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
    queryKey: ['verb-social-neg'], queryFn: () => fetch(apiUrl('/api/admindb?table=social_enriched&sentiment=negative&limit=15')).then(r => r.json()),
  })
  const { data: socialPos } = useQuery<{ rows: Record<string, unknown>[] }>({
    queryKey: ['verb-social-pos'], queryFn: () => fetch(apiUrl('/api/admindb?table=social_enriched&sentiment=positive&limit=15')).then(r => r.json()),
  })
  const { data: reviewNeg } = useQuery<{ rows: Record<string, unknown>[] }>({
    queryKey: ['verb-review-neg'], queryFn: () => fetch(apiUrl('/api/admindb?table=review_enriched&sentiment=negative&limit=10')).then(r => r.json()),
  })
  const { data: reviewPos } = useQuery<{ rows: Record<string, unknown>[] }>({
    queryKey: ['verb-review-pos'], queryFn: () => fetch(apiUrl('/api/admindb?table=review_enriched&sentiment=positive&limit=10')).then(r => r.json()),
  })

  const all: any[] = [
    ...(socialNeg?.rows || []).map(r => ({ ...r, _sent: 'neg' })),
    ...(socialPos?.rows || []).map(r => ({ ...r, _sent: 'pos' })),
    ...(reviewNeg?.rows || []).map(r => ({ ...r, _sent: 'neg' })),
    ...(reviewPos?.rows || []).map(r => ({ ...r, _sent: 'pos' })),
  ].filter(r => {
    const text = String(r.summary_short || r.body || r.text || '')
    return text.length > 40 && isFrench(text)
  })

  // Stable shuffle
  const verbatims = [...all].sort((a, b) => {
    const ha = String(a.summary_short || '').length; const hb = String(b.summary_short || '').length
    return ha - hb
  }).slice(0, 8)

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
  const entity = String(current?.entity_name || '')
  const isNeg = current._sent === 'neg'

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 mb-3"
      onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Verbatims en direct</h3>
        <div className="flex gap-1">
          {verbatims.map((_, i) => (
            <button key={i} onClick={() => setIdx(i)}
              className={`w-2 h-2 rounded-full transition-all ${i === idx ? (isNeg ? 'bg-red-400' : 'bg-green-400') : 'bg-gray-200'}`} />
          ))}
        </div>
      </div>

      <div className={`rounded-xl p-3 ${isNeg ? 'bg-red-50/60 border-l-[3px] border-red-300' : 'bg-green-50/60 border-l-[3px] border-green-300'}`}>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-base">{platform.icon}</span>
          <span className="text-[11px] font-bold text-gray-700">{entity || platform.label}</span>
          <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold ${isNeg ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}`}>
            {isNeg ? 'Négatif' : 'Positif'}
          </span>
        </div>
        <p className="text-[12px] text-gray-700 italic leading-relaxed">"{text.slice(0, 200)}{text.length > 200 ? '...' : ''}"</p>
        <div className="text-[9px] text-gray-400 mt-2">
          {current?.rating ? `${'★'.repeat(Math.round(Number(current.rating)))}` : ''} {platform.label} • {(String(current?.published_at || '')).slice(0, 10)}
        </div>
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
        <div className="bg-[#0f172a] rounded-xl px-4 py-3">
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">NPS Proxy</div>
          <div className={`text-[28px] font-black leading-none ${kpis.nps_proxy > 20 ? 'text-emerald-400' : kpis.nps_proxy < 0 ? 'text-red-500' : 'text-orange-400'}`}>
            {kpis.nps_proxy > 0 ? '+' : ''}{kpis.nps_proxy}
          </div>
        </div>
        <div className="bg-[#0f172a] rounded-xl px-4 py-3">
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Note moyenne</div>
          <div className="text-[26px] font-black text-amber-400 leading-none">{kpis.avg_rating} ★</div>
        </div>
        <div className="bg-[#0f172a] rounded-xl px-4 py-3">
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">SAV négatif</div>
          <div className="text-[26px] font-black text-red-500 leading-none">{Math.round(kpis.sav_negative_pct * 100)}%</div>
        </div>
        <div className="bg-[#0f172a] rounded-xl px-4 py-3">
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Total avis</div>
          <div className="text-[26px] font-black text-white leading-none">{kpis.total_reviews.toLocaleString('fr-FR')}</div>
        </div>
      </div>

      {/* Irritants + Enchantements (barres only, no carousel inside) */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-[10px] font-semibold text-red-400 uppercase tracking-wide mb-3">Top irritants (avis 1-2★)</h3>
          {irritants.slice(0, 4).map((item, i) => (
            <div key={i} className="mb-2.5">
              <div className="flex justify-between mb-1">
                <span className="text-[11px] text-gray-700 font-medium">{IRRITANT_RENAME[item.label] || item.label}</span>
                <span className="text-[11px] text-gray-400 font-semibold">{item.count} <span className="text-[9px]">({item.pct}%)</span></span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-red-400 rounded-full" style={{ width: `${item.bar_pct}%` }} />
              </div>
            </div>
          ))}
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-[10px] font-semibold text-green-500 uppercase tracking-wide mb-3">Top enchantements (avis 5★)</h3>
          {enchantements.slice(0, 3).map((item, i) => (
            <div key={i} className="mb-2.5">
              <div className="flex justify-between mb-1">
                <span className="text-[11px] text-gray-700 font-medium">{ENCHANT_RENAME[item.label] || item.label}</span>
                <span className="text-[11px] text-gray-400 font-semibold">{item.count} <span className="text-[9px]">({item.pct}%)</span></span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-green-500 rounded-full" style={{ width: `${item.bar_pct}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Verbatim carousel — standalone, all sources, FR only */}
      <VerbatimCarousel />

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
          <strong className="text-blue-600">PRIORITAIRE :</strong> Chatbot SAV première réponse. {Math.round(kpis.sav_negative_pct * 100)}% des avis négatifs = SAV.
          <span className="text-emerald-600 font-bold ml-1">Objectif : NPS +15 pts Q3 2026.</span>
        </p>
      </div>
    </div>
  )
}

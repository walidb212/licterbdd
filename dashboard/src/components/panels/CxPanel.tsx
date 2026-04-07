import { useState, useEffect } from 'react'
import { useCx, apiUrl } from '../../api/client'
import { useQuery } from '@tanstack/react-query'

// Rename duplicates between irritants/enchantements
const IRRITANT_RENAME: Record<string, string> = {
  'Rapport qualité/prix': 'Qualité insuffisante vs prix',
  'Attente en caisse': 'Files d\'attente',
}
const ENCHANT_RENAME: Record<string, string> = {
  'Rapport qualité/prix': 'Excellent rapport qualité/prix',
  'Attente en caisse': 'Rapidité en magasin',
  'choix en rayon': 'Large choix produits',
}

// Verbatim carousel component
function VerbatimCarousel({ type }: { type: 'negative' | 'positive' }) {
  const [idx, setIdx] = useState(0)
  const [paused, setPaused] = useState(false)

  const { data } = useQuery<{ rows: { summary_short?: string; body?: string; text?: string; source_name?: string; rating?: number; published_at?: string }[] }>({
    queryKey: ['verbatims', type],
    queryFn: () => fetch(apiUrl(`/api/admindb?table=${type === 'negative' ? 'review_enriched' : 'review_enriched'}&sentiment=${type}&limit=5`)).then(r => r.json()),
  })

  const verbatims = (data?.rows || []).filter(r => {
    const text = r.summary_short || r.body || r.text || ''
    return text.length > 30
  }).slice(0, 5)

  useEffect(() => {
    if (paused || !verbatims.length) return
    const timer = setInterval(() => setIdx(i => (i + 1) % verbatims.length), 4000)
    return () => clearInterval(timer)
  }, [paused, verbatims.length])

  if (!verbatims.length) return null

  const current = verbatims[idx]
  const text = current?.summary_short || current?.body || current?.text || ''
  const isNeg = type === 'negative'

  return (
    <div
      className={`mt-3 rounded-xl p-3 border-l-3 ${isNeg ? 'bg-red-50/50 border-l-red-300' : 'bg-green-50/50 border-l-green-300'}`}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <p className="text-[11px] text-gray-600 italic leading-relaxed">"{text.slice(0, 150)}{text.length > 150 ? '...' : ''}"</p>
      <div className="flex items-center justify-between mt-2">
        <span className="text-[9px] text-gray-400">
          {current?.rating ? `${'★'.repeat(Math.round(current.rating))}` : ''} {current?.source_name || ''} • {(current?.published_at || '').slice(0, 10)}
        </span>
        <div className="flex gap-1">
          {verbatims.map((_, i) => (
            <button key={i} onClick={() => setIdx(i)}
              className={`w-1.5 h-1.5 rounded-full transition-all ${i === idx ? (isNeg ? 'bg-red-400' : 'bg-green-400') : 'bg-gray-200'}`} />
          ))}
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
      {/* 4 KPIs — dark style */}
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
          <div className="text-[10px] text-gray-500">{kpis.total_reviews.toLocaleString('fr-FR')} avis</div>
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

      {/* Irritants + Enchantements with verbatim carousels */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        {/* Irritants */}
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-[10px] font-semibold text-red-400 uppercase tracking-wide mb-3">Top irritants (avis 1-2★)</h3>
          {irritants.length === 0
            ? <p className="text-gray-400 text-xs">Données insuffisantes.</p>
            : irritants.slice(0, 4).map((item, i) => (
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
          <VerbatimCarousel type="negative" />
        </div>

        {/* Enchantements */}
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-[10px] font-semibold text-green-500 uppercase tracking-wide mb-3">Top enchantements (avis 5★)</h3>
          {enchantements.length === 0
            ? <p className="text-gray-400 text-xs">Données insuffisantes.</p>
            : enchantements.slice(0, 3).map((item, i) => (
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
          <VerbatimCarousel type="positive" />
        </div>
      </div>

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

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiUrl } from '../../api/client'

interface DbResult {
  table: string; tables: string[]; table_stats: Record<string, number>;
  columns: string[]; total: number; limit: number; offset: number;
  rows: Record<string, unknown>[]; filters: Record<string, string>;
}

function getSourceUrl(row: Record<string, unknown>): string | null {
  const key = String(row.item_key || '')
  const source = String(row.source_name || row.platform || '')
  const entity = String(row.entity_name || '')
  // X/Twitter (key format: x_post:2041262069631140086)
  if (source === 'x_post' && key.includes('x_post:')) {
    const tweetId = key.replace('x_post:', '')
    if (/^\d+$/.test(tweetId)) return `https://x.com/i/status/${tweetId}`
  }
  // Reddit (key format: reddit_post:https://www.reddit.com/r/.../comments/... | title)
  if ((source === 'reddit_post' || source === 'reddit_comment') && key.includes('http')) {
    const urlMatch = key.match(/(https?:\/\/www\.reddit\.com\/r\/[^\s|]+)/)
    if (urlMatch) return urlMatch[1]
  }
  // YouTube (key format: youtube_video:0b9beGgfCwE)
  if (source === 'youtube_video' && key.includes('youtube_video:')) {
    const videoId = key.replace('youtube_video:', '')
    return `https://www.youtube.com/watch?v=${videoId}`
  }
  if (source === 'youtube_comment' && key.includes('youtube_comment:')) {
    const videoId = key.replace('youtube_comment:', '').split('_')[0]
    return `https://www.youtube.com/watch?v=${videoId}`
  }
  // TikTok (key format: tiktok_video:7624473316539075862)
  if (source === 'tiktok_video' && key.includes('tiktok_video:')) {
    const videoId = key.replace('tiktok_video:', '')
    return `https://www.tiktok.com/@${entity}/video/${videoId}`
  }
  // Facebook Ads -> Meta Ad Library
  if (source === 'facebook_ad') {
    const brandName = String(row.brand_focus || 'decathlon')
    return `https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=FR&q=${brandName}`
  }
  // Instagram
  if (source === 'instagram_post' && entity) {
    return `https://www.instagram.com/${entity.replace('@', '')}/`
  }
  // Trustpilot / review sites
  if (source === 'review_site' && entity.toLowerCase().includes('decathlon')) {
    return 'https://fr.trustpilot.com/review/www.decathlon.fr'
  }
  if (source === 'review_site' && entity.toLowerCase().includes('intersport')) {
    return 'https://fr.trustpilot.com/review/www.intersport.fr'
  }
  return null
}

const SENT_COLORS: Record<string, string> = {
  positive: 'text-green-600 bg-green-50', negative: 'text-red-500 bg-red-50',
  neutral: 'text-gray-500 bg-gray-50', mixed: 'text-amber-500 bg-amber-50',
}

const SOURCE_OPTIONS = [
  { value: '', label: 'Toutes sources' },
  { value: 'reddit_post', label: 'Reddit (posts)' },
  { value: 'reddit_comment', label: 'Reddit (comments)' },
  { value: 'youtube_video', label: 'YouTube (vidéos)' },
  { value: 'youtube_comment', label: 'YouTube (comments)' },
  { value: 'tiktok_video', label: 'TikTok' },
  { value: 'x_post', label: 'X / Twitter' },
  { value: 'instagram_post', label: 'Instagram' },
  { value: 'facebook_ad', label: 'Facebook Ads' },
  { value: 'news_article', label: 'Presse' },
  { value: 'store_review', label: 'Google Maps' },
  { value: 'review_site', label: 'Avis (Trustpilot...)' },
]

const DATASET_TABS = [
  { table: 'social_enriched', label: 'Social' },
  { table: 'review_enriched', label: 'Avis clients' },
  { table: 'news_enriched', label: 'Presse' },
  { table: 'store_reviews', label: 'Google Maps' },
  { table: 'entity_summaries', label: 'Entités' },
]

export default function AdminDbPanel() {
  const [table, setTable] = useState('social_enriched')
  const [search, setSearch] = useState('')
  const [source, setSource] = useState('')
  const [brand, setBrand] = useState('')
  const [sentiment, setSentiment] = useState('')
  const [page, setPage] = useState(0)

  const params = new URLSearchParams({ table, limit: '25', offset: String(page * 25) })
  if (search) params.set('search', search)
  if (source) params.set('source', source)
  if (brand) params.set('brand', brand)
  if (sentiment) params.set('sentiment', sentiment)

  const { data, isLoading } = useQuery<DbResult>({
    queryKey: ['admindb', table, search, source, brand, sentiment, page],
    queryFn: () => fetch(apiUrl(`/api/admindb?${params}`)).then(r => r.json()),
  })

  const totalRecords = Object.values(data?.table_stats || {}).reduce((s, v) => s + v, 0)

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-gray-800">Explorateur de données</h2>
          <p className="text-[11px] text-gray-400">{totalRecords.toLocaleString()} records en base, {Object.keys(data?.table_stats || {}).length} tables</p>
        </div>
      </div>

      {/* Dataset tabs */}
      <div className="flex gap-1.5 mb-4">
        {DATASET_TABS.map(t => {
          const count = data?.table_stats?.[t.table] || 0
          return (
            <button key={t.table} onClick={() => { setTable(t.table); setPage(0); setSource(''); }}
              className={`px-3 py-1.5 rounded-full text-[11px] font-medium transition-all
                ${t.table === table ? 'bg-[#324DE6] text-white shadow-sm' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>
              {t.label} {count > 0 && <span className="opacity-60">({count.toLocaleString()})</span>}
            </button>
          )
        })}
      </div>

      {/* Filters row */}
      <div className="flex gap-2 mb-4">
        <input value={search} onChange={e => { setSearch(e.target.value); setPage(0); }}
          placeholder="Rechercher..." className="flex-1 bg-white border border-gray-200 rounded-lg px-3 py-2 text-[12px] outline-none focus:border-[#324DE6] shadow-sm" />
        <select value={brand} onChange={e => { setBrand(e.target.value); setPage(0); }}
          className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-[12px] shadow-sm">
          <option value="">Toutes marques</option>
          <option value="decathlon">Decathlon</option>
          <option value="intersport">Intersport</option>
        </select>
        <select value={sentiment} onChange={e => { setSentiment(e.target.value); setPage(0); }}
          className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-[12px] shadow-sm">
          <option value="">Tous sentiments</option>
          <option value="positive">Positif</option>
          <option value="negative">Négatif</option>
          <option value="neutral">Neutre</option>
          <option value="mixed">Mixte</option>
        </select>
        {table === 'social_enriched' && (
          <select value={source} onChange={e => { setSource(e.target.value); setPage(0); }}
            className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-[12px] shadow-sm">
            {SOURCE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        )}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] text-gray-400">
          {isLoading ? 'Chargement...' : `${(data?.total || 0).toLocaleString()} résultats – page ${page + 1}`}
        </span>
        <div className="flex gap-1">
          <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
            className="px-3 py-1 rounded-lg text-[11px] bg-white border border-gray-200 disabled:opacity-30 shadow-sm hover:bg-gray-50">Préc</button>
          <button onClick={() => setPage(page + 1)} disabled={(data?.rows?.length || 0) < 25}
            className="px-3 py-1 rounded-lg text-[11px] bg-white border border-gray-200 disabled:opacity-30 shadow-sm hover:bg-gray-50">Suiv</button>
        </div>
      </div>

      {/* Data cards */}
      <div className="space-y-2">
        {(data?.rows || []).map((row, i) => {
          const textField = row.summary_short || row.text || row.body || row.executive_takeaway || ''
          const sentimentVal = String(row.sentiment_label || row.sentiment || row.sentiment_detected || '')
          const sentStyle = SENT_COLORS[sentimentVal] || 'text-gray-400 bg-gray-50'
          const brandVal = String(row.brand_focus || row.brand || '')
          const sourceVal = String(row.source_name || row.platform || row.source_partition || '')
          const url = getSourceUrl(row)

          return (
            <div key={i} className={`bg-white rounded-xl border border-gray-100 p-3 hover:border-gray-200 transition-all shadow-sm ${url ? 'cursor-pointer hover:bg-blue-50/30' : ''}`}
              onClick={() => url && window.open(url, '_blank')}>
              <div className="flex flex-wrap items-center gap-1.5 mb-2">
                {brandVal && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${brandVal === 'decathlon' ? 'bg-blue-50 text-blue-600' : brandVal === 'intersport' ? 'bg-red-50 text-red-500' : 'bg-gray-50 text-gray-500'}`}>
                    {brandVal}
                  </span>
                )}
                {sourceVal && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 font-medium">{sourceVal}</span>
                )}
                {sentimentVal && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${sentStyle}`}>{sentimentVal}</span>
                )}
                {row.topic && String(row.topic) !== 'general' && String(row.topic) !== 'general_brand_signal' && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-50 text-purple-500 font-medium">{String(row.topic).replace(/_/g, ' ')}</span>
                )}
                {row.rating && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-yellow-50 text-yellow-600 font-bold">{String(row.rating)}★</span>
                )}
              </div>

              <div className="text-[12px] text-gray-700 leading-relaxed">
                {String(textField).slice(0, 300)}{String(textField).length > 300 ? '...' : ''}
              </div>

              <div className="flex items-center gap-3 mt-2 text-[10px] text-gray-400">
                {row.published_at && <span>{String(row.published_at).slice(0, 10)}</span>}
                {row.entity_name && <span>{String(row.entity_name)}</span>}
                {url && <span className="text-blue-400 ml-auto">Voir la source ↗</span>}
                {row.category && <span>{String(row.category)}</span>}
                {row.volume_items && <span>{String(row.volume_items)} mentions</span>}
              </div>
            </div>
          )
        })}
      </div>

      {(!data?.rows?.length && !isLoading) && (
        <div className="text-center py-8 text-gray-400 text-sm">Aucun résultat pour ces filtres.</div>
      )}
    </div>
  )
}

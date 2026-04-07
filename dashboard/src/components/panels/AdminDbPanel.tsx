import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiUrl } from '../../api/client'

interface DbResult {
  table: string; tables: string[]; table_stats: Record<string, number>;
  columns: string[]; total: number; limit: number; offset: number;
  rows: Record<string, unknown>[]; filters: Record<string, string>;
}

const TABLE_LABELS: Record<string, string> = {
  social_enriched: 'Social',
  review_enriched: 'Avis',
  news_enriched: 'Presse',
  entity_summaries: 'Entités',
  excel_reputation: 'Crise (Excel)',
  excel_benchmark: 'Benchmark (Excel)',
  excel_cx: 'CX (Excel)',
  store_reviews: 'Google Maps',
}

const DISPLAY_COLS: Record<string, string[]> = {
  social_enriched: ['brand_focus', 'source_name', 'sentiment_label', 'topic', 'post_type', 'summary_short'],
  review_enriched: ['brand_focus', 'source_name', 'sentiment_label', 'rating', 'topic', 'summary_short'],
  news_enriched: ['brand_focus', 'source_name', 'sentiment_label', 'topic', 'summary_short'],
  entity_summaries: ['entity_name', 'source_partition', 'brand_focus', 'volume_items', 'dominant_sentiment', 'executive_takeaway'],
  excel_reputation: ['platform', 'sentiment', 'text'],
  excel_benchmark: ['brand', 'platform', 'topic', 'sentiment_detected', 'text'],
  excel_cx: ['brand_focus', 'platform', 'category', 'rating', 'sentiment', 'text'],
  store_reviews: ['brand_focus', 'entity_name', 'rating', 'body'],
}

const COL_LABELS: Record<string, string> = {
  brand_focus: 'Marque', source_name: 'Source', sentiment_label: 'Sentiment',
  summary_short: 'Résumé', topic: 'Topic', post_type: 'Type', rating: 'Note',
  entity_name: 'Entité', source_partition: 'Partition', volume_items: 'Volume',
  dominant_sentiment: 'Sentiment', executive_takeaway: 'Analyse', platform: 'Plateforme',
  sentiment: 'Sentiment', text: 'Texte', brand: 'Marque', category: 'Catégorie',
  body: 'Texte', sentiment_detected: 'Sentiment',
}

const SENT_COLORS: Record<string, string> = {
  positive: 'text-green-600 bg-green-50', negative: 'text-red-500 bg-red-50',
  neutral: 'text-gray-500 bg-gray-50', mixed: 'text-amber-500 bg-amber-50',
}

export default function AdminDbPanel() {
  const [table, setTable] = useState('social_enriched')
  const [search, setSearch] = useState('')
  const [source, setSource] = useState('')
  const [brand, setBrand] = useState('')
  const [sentiment, setSentiment] = useState('')
  const [page, setPage] = useState(0)

  const params = new URLSearchParams({ table, limit: '20', offset: String(page * 20) })
  if (search) params.set('search', search)
  if (source) params.set('source', source)
  if (brand) params.set('brand', brand)
  if (sentiment) params.set('sentiment', sentiment)

  const { data, isLoading } = useQuery<DbResult>({
    queryKey: ['admindb', table, search, source, brand, sentiment, page],
    queryFn: () => fetch(apiUrl(`/api/admindb?${params}`)).then(r => r.json()),
  })

  const cols = DISPLAY_COLS[table] || data?.columns?.slice(0, 6) || []
  const totalRecords = Object.values(data?.table_stats || {}).reduce((s, v) => s + v, 0)

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-gray-800">Base de données</h2>
          <p className="text-[11px] text-gray-400">{totalRecords.toLocaleString()} records across {Object.keys(data?.table_stats || {}).length} tables</p>
        </div>
      </div>

      {/* Table tabs */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {Object.entries(data?.table_stats || {}).map(([t, count]) => (
          <button key={t} onClick={() => { setTable(t); setPage(0); }}
            className={`px-3 py-1.5 rounded-full text-[11px] font-medium transition-all
              ${t === table ? 'bg-[#324DE6] text-white shadow-sm' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>
            {TABLE_LABELS[t] || t} <span className="opacity-60">({count})</span>
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4">
        <input value={search} onChange={e => { setSearch(e.target.value); setPage(0); }}
          placeholder="Rechercher dans les textes..." className="flex-1 bg-white border border-gray-200 rounded-lg px-3 py-2 text-[12px] outline-none focus:border-[#324DE6] shadow-sm" />
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
        </select>
        <select value={source} onChange={e => { setSource(e.target.value); setPage(0); }}
          className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-[12px] shadow-sm">
          <option value="">Toutes sources</option>
          <option value="reddit_post">Reddit</option>
          <option value="youtube_video">YouTube</option>
          <option value="tiktok_video">TikTok</option>
          <option value="x_post">X/Twitter</option>
          <option value="news_article">Presse</option>
          <option value="social">Social</option>
          <option value="customer">Avis clients</option>
          <option value="community">Communauté</option>
        </select>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] text-gray-400">
          {isLoading ? 'Chargement...' : `${(data?.total || 0).toLocaleString()} résultats — page ${page + 1}`}
        </span>
        <div className="flex gap-1">
          <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
            className="px-3 py-1 rounded-lg text-[11px] bg-white border border-gray-200 disabled:opacity-30 shadow-sm hover:bg-gray-50">← Préc</button>
          <button onClick={() => setPage(page + 1)} disabled={(data?.rows?.length || 0) < 20}
            className="px-3 py-1 rounded-lg text-[11px] bg-white border border-gray-200 disabled:opacity-30 shadow-sm hover:bg-gray-50">Suiv →</button>
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

          return (
            <div key={i} className="bg-white rounded-xl border border-gray-100 p-3 hover:border-gray-200 transition-all shadow-sm">
              {/* Top row: badges */}
              <div className="flex flex-wrap items-center gap-1.5 mb-2">
                {brandVal && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${brandVal === 'decathlon' ? 'bg-blue-50 text-blue-600' : 'bg-red-50 text-red-500'}`}>
                    {brandVal}
                  </span>
                )}
                {sourceVal && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 font-medium">{sourceVal}</span>
                )}
                {sentimentVal && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${sentStyle}`}>{sentimentVal}</span>
                )}
                {row.topic && String(row.topic) !== 'general' && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-50 text-purple-500 font-medium">{String(row.topic)}</span>
                )}
                {row.post_type && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 font-medium">{String(row.post_type)}</span>
                )}
                {row.rating && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-yellow-50 text-yellow-600 font-bold">{String(row.rating)}★</span>
                )}
                {row.priority_score && Number(row.priority_score) > 50 && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-50 text-red-500 font-bold">prio {String(row.priority_score)}</span>
                )}
              </div>

              {/* Text */}
              <div className="text-[12px] text-gray-700 leading-relaxed">
                {String(textField).slice(0, 300)}{String(textField).length > 300 ? '...' : ''}
              </div>

              {/* Meta row */}
              <div className="flex items-center gap-3 mt-2 text-[10px] text-gray-400">
                {row.published_at && <span>{String(row.published_at).slice(0, 10)}</span>}
                {row.entity_name && <span>{String(row.entity_name)}</span>}
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

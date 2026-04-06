import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiUrl } from '../../api/client'

interface DbResult {
  table: string; tables: string[]; table_stats: Record<string, number>;
  columns: string[]; total: number; limit: number; offset: number;
  rows: Record<string, unknown>[]; filters: Record<string, string>;
  error?: string;
}

export default function AdminDbPanel() {
  const [table, setTable] = useState('social_enriched')
  const [search, setSearch] = useState('')
  const [source, setSource] = useState('')
  const [brand, setBrand] = useState('')
  const [sentiment, setSentiment] = useState('')
  const [page, setPage] = useState(0)

  const params = new URLSearchParams({ table, limit: '30', offset: String(page * 30) })
  if (search) params.set('search', search)
  if (source) params.set('source', source)
  if (brand) params.set('brand', brand)
  if (sentiment) params.set('sentiment', sentiment)

  const { data, isLoading } = useQuery<DbResult>({
    queryKey: ['admindb', table, search, source, brand, sentiment, page],
    queryFn: () => fetch(apiUrl(`/api/admindb?${params}`)).then(r => r.json()),
  })

  return (
    <div>
      <h2 className="text-lg font-bold text-gray-800 mb-1">Admin DB Explorer</h2>
      <p className="text-[11px] text-gray-400 mb-4">Explorez les données brutes de la base SQLite</p>

      {/* Table selector */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {(data?.tables || []).map(t => (
          <button key={t} onClick={() => { setTable(t); setPage(0); }}
            className={`px-3 py-1.5 rounded-full text-[11px] font-medium transition-all
              ${t === table ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>
            {t} <span className="opacity-60">({data?.table_stats?.[t] || 0})</span>
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4">
        <input value={search} onChange={e => { setSearch(e.target.value); setPage(0); }}
          placeholder="Rechercher..." className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-[12px] outline-none focus:border-blue-400" />
        <select value={brand} onChange={e => { setBrand(e.target.value); setPage(0); }}
          className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-[12px]">
          <option value="">Toutes marques</option>
          <option value="decathlon">Decathlon</option>
          <option value="intersport">Intersport</option>
        </select>
        <select value={sentiment} onChange={e => { setSentiment(e.target.value); setPage(0); }}
          className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-[12px]">
          <option value="">Tous sentiments</option>
          <option value="positive">Positif</option>
          <option value="negative">Négatif</option>
          <option value="neutral">Neutre</option>
          <option value="mixed">Mixte</option>
        </select>
        <select value={source} onChange={e => { setSource(e.target.value); setPage(0); }}
          className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-[12px]">
          <option value="">Toutes sources</option>
          <option value="reddit_post">Reddit</option>
          <option value="youtube_video">YouTube</option>
          <option value="tiktok_video">TikTok</option>
          <option value="x_post">X/Twitter</option>
          <option value="news_article">Presse</option>
          <option value="review_site">Avis</option>
          <option value="store">Google Maps</option>
          <option value="social">Social</option>
          <option value="customer">Customer</option>
          <option value="employee">Employee</option>
          <option value="community">Community</option>
        </select>
      </div>

      {/* Results count */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] text-gray-400">
          {isLoading ? 'Chargement...' : `${data?.total || 0} résultats — page ${page + 1}`}
        </span>
        <div className="flex gap-1">
          <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
            className="px-2 py-1 rounded text-[11px] bg-gray-100 disabled:opacity-30">← Préc</button>
          <button onClick={() => setPage(page + 1)} disabled={(data?.rows?.length || 0) < 30}
            className="px-2 py-1 rounded text-[11px] bg-gray-100 disabled:opacity-30">Suiv →</button>
        </div>
      </div>

      {/* Data table */}
      <div className="bg-white rounded-[20px] shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="bg-gray-50">
                {(data?.columns || []).slice(0, 8).map(col => (
                  <th key={col} className="text-left py-2 px-3 font-semibold text-gray-400 uppercase tracking-wider text-[9px]">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(data?.rows || []).map((row, i) => (
                <tr key={i} className="border-t border-gray-50 hover:bg-blue-50/30">
                  {(data?.columns || []).slice(0, 8).map(col => {
                    let val = String(row[col] ?? '')
                    if (val.length > 100) val = val.slice(0, 100) + '...'
                    // Color sentiment
                    const isSentiment = col === 'sentiment_label'
                    const sentColor = isSentiment ? (val === 'positive' ? 'text-green-600' : val === 'negative' ? 'text-red-500' : 'text-gray-400') : ''
                    return (
                      <td key={col} className={`py-2 px-3 ${sentColor}`}>{val}</td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

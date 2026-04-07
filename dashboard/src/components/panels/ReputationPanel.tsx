import { useReputation, apiUrl } from '../../api/client'
import { useQuery } from '@tanstack/react-query'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import WordCloud from '../../charts/WordCloud'

interface CrisisData {
  timeline: { date: string; volume: number; negative: number }[]
  peak_day: { date: string; volume: number } | null
  avg_daily_volume: number
  severity: string
  is_escalating: boolean
  warnings: string[]
}

const PLAYBOOK = [
  { time: 'H+0', label: 'Alerte COMEX', detail: 'DirCom + Directeur Qualité + CEO', color: 'bg-red-500' },
  { time: 'H+2', label: 'Réponse publique', detail: 'Top 10 posts viraux avec réponse officielle', color: 'bg-red-400' },
  { time: 'H+6', label: 'Communiqué interne', detail: 'Points de vente + équipes SAV alertés', color: 'bg-orange-400' },
  { time: 'H+24', label: 'FAQ dédiée', detail: 'Page créée sur decathlon.fr avec procédure', color: 'bg-amber-400' },
  { time: 'H+48', label: 'Bilan sentiment', detail: 'Si pas d\'amélioration → rappel produit', color: 'bg-yellow-400' },
  { time: 'J+7', label: 'Rapport de crise', detail: 'Impact + mesures correctives + KPIs', color: 'bg-green-400' },
]

export default function ReputationPanel() {
  const { data, isLoading, error } = useReputation()
  const { data: crisis } = useQuery<CrisisData>({ queryKey: ['crisis'], queryFn: () => fetch(apiUrl('/api/crisis')).then(r => r.json()) })

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur de chargement.</div>

  const { kpis, alert } = data
  const caMenuce = (data as any).ca_menace_m || Math.round(kpis.sentiment_negatif_pct * 4500 * 0.15)
  const timeline = (crisis?.timeline || []).slice(-14).map(d => ({
    date: d.date.slice(5), volume: d.volume, negative: d.negative,
  }))
  const maxNeg = Math.max(...timeline.map(d => d.negative || 0), 1)

  return (
    <div>
      {/* Alert banner */}
      {alert.active && (
        <div className="relative bg-gradient-to-r from-red-600 to-red-700 rounded-xl px-5 py-2 mb-3 overflow-hidden">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
              <span className="text-white font-bold text-[12px]">CRISE ACTIVE — Vélo défectueux</span>
              <span className="text-white/80 text-[11px]">Gravity : <strong className="text-white">{kpis.gravity_score}/10</strong></span>
            </div>
            <span className="bg-white/20 text-white text-[9px] font-bold px-2 py-0.5 rounded-full animate-pulse">LIVE</span>
          </div>
        </div>
      )}

      {/* 4 KPIs */}
      <div className="grid grid-cols-4 gap-2 mb-3">
        <div className="bg-white shadow-sm border border-gray-100 rounded-xl px-4 py-3">
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Gravity Score</div>
          <div className="text-[28px] font-black text-red-500 leading-none">{kpis.gravity_score}<span className="text-[14px] text-red-400">/10</span></div>
        </div>
        <div className="bg-white shadow-sm border border-gray-100 rounded-xl px-4 py-3">
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Volume mentions</div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-[26px] font-black text-gray-900 leading-none">{kpis.volume_total.toLocaleString('fr-FR')}</span>
            <span className="text-[10px] font-bold text-emerald-400">↑+190%</span>
          </div>
        </div>
        <div className="bg-white shadow-sm border border-gray-100 rounded-xl px-4 py-3">
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Sentiment négatif</div>
          <div className="text-[26px] font-black text-orange-400 leading-none">{Math.round(kpis.sentiment_negatif_pct * 100)}%</div>
        </div>
        <div className="bg-white shadow-sm border border-gray-100 rounded-xl px-4 py-3 relative">
          <div className="absolute top-2 right-2 text-[14px]">⚠️</div>
          <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1">CA menacé</div>
          <div className="text-[26px] font-black text-red-500 leading-none">{caMenuce}M€</div>
        </div>
      </div>

      {/* Row: Left (timeline + reco + playbook) | Right (word cloud) */}
      <div className="grid grid-cols-2 gap-2">
        <div className="flex flex-col gap-2">
          {/* Timeline */}
          <div className="bg-white rounded-xl p-3 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Timeline crise — 14j</h3>
              {crisis?.is_escalating && <span className="text-[9px] font-bold text-red-400 bg-red-50 px-2 py-0.5 rounded-full animate-pulse">EN HAUSSE</span>}
            </div>
            {timeline.length > 0 ? (
              <ResponsiveContainer width="100%" height={100}>
                <AreaChart data={timeline} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gVol" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02}/>
                    </linearGradient>
                    <linearGradient id="gNeg" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0.05}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" tick={{ fill: '#9ca3af', fontSize: 9 }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="vol" tick={{ fill: '#9ca3af', fontSize: 9 }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="neg" orientation="right" tick={false} axisLine={false} tickLine={false} domain={[0, maxNeg * 3]} />
                  <Tooltip contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, fontSize: 11 }} formatter={(v: number, n: string) => [v, n === 'volume' ? '📊 Volume' : '🔴 Négatif']} />
                  <Area yAxisId="vol" type="monotone" dataKey="volume" stroke="#3b82f6" strokeWidth={2} fill="url(#gVol)" />
                  <Area yAxisId="neg" type="monotone" dataKey="negative" stroke="#ef4444" strokeWidth={2.5} fill="url(#gNeg)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : <div className="text-gray-400 text-xs text-center py-4">Timeline non disponible</div>}
            {crisis?.peak_day && (
              <div className="flex items-center gap-2 mt-1 text-[10px] text-gray-500 bg-amber-50 rounded-lg px-3 py-1">
                <span className="w-3.5 h-3.5 rounded-full bg-amber-400 text-white text-[8px] font-bold flex items-center justify-center shrink-0">A</span>
                <span>Pic <strong className="text-gray-700">{crisis.peak_day.date}</strong> — {crisis.peak_day.volume} mentions — <strong className="text-amber-600">+{Math.round((crisis.peak_day.volume / (crisis.avg_daily_volume || 1) - 1) * 100)}%</strong></span>
              </div>
            )}
          </div>

          {/* Reco critique */}
          <div className="bg-red-50 border-l-4 border-red-600 rounded-r-xl px-4 py-2">
            <p className="text-[11px] text-gray-800">
              <strong className="text-red-600">CRITIQUE :</strong> Communiqué de crise vélo — 48h max.
              <span className="text-emerald-600 font-bold ml-1">Impact : -60% négatif en 7j.</span>
            </p>
          </div>

          {/* Smart Playbook */}
          <div className="bg-white rounded-xl p-3 shadow-sm border border-gray-100">
            <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-2">Smart Playbook — Plan d'action</h3>
            <div className="space-y-1.5">
              {PLAYBOOK.map((step, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className={`${step.color} text-white text-[9px] font-bold px-1.5 py-0.5 rounded w-9 text-center shrink-0`}>{step.time}</span>
                  <span className="text-[11px] font-semibold text-gray-700">{step.label}</span>
                  <span className="text-[10px] text-gray-400 truncate">{step.detail}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT: Word Cloud */}
        <div className="bg-[#f8fafc] rounded-xl p-4 shadow-sm border border-gray-100 flex items-center">
          <WordCloud />
        </div>
      </div>
    </div>
  )
}

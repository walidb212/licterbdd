import { useReputation } from '../../api/client'
import { useQuery } from '@tanstack/react-query'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceDot } from 'recharts'
import WordCloud from '../../charts/WordCloud'

interface CrisisData {
  timeline: { date: string; volume: number; negative: number; neg_pct: number; is_spike: boolean }[]
  peak_day: { date: string; volume: number } | null
  avg_daily_volume: number
  severity: string
  is_escalating: boolean
  warnings: string[]
}

export default function ReputationPanel() {
  const { data, isLoading, error } = useReputation()
  const { data: crisis } = useQuery<CrisisData>({ queryKey: ['crisis'], queryFn: () => fetch('/api/crisis').then(r => r.json()) })

  if (isLoading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Chargement...</div>
  if (error || !data) return <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-500 text-sm">Erreur de chargement.</div>

  const { kpis, alert, volume_by_day } = data
  const caMenuce = (data as any).ca_menace_m || Math.round(kpis.sentiment_negatif_pct * 4500 * 0.15)

  const timelineData = (crisis?.timeline || volume_by_day).slice(-14).map(d => ({
    ...d,
    date: d.date.slice(5),
    negative: 'negative' in d ? d.negative : 0,
  }))

  return (
    <div>
      {/* === ALERTE CRISE — pleine largeur, rouge vif === */}
      {alert.active && (
        <div className="relative bg-gradient-to-r from-red-600 to-red-700 rounded-2xl px-6 py-4 mb-5 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent animate-[alert-sweep_3s_infinite]" />
          <div className="flex items-center justify-between relative">
            <div className="flex items-center gap-3">
              <span className="w-3 h-3 rounded-full bg-white animate-pulse" />
              <span className="text-white font-bold text-[14px]">CRISE ACTIVE — Vélo défectueux</span>
              <span className="text-white/80 text-[13px]">Gravity Score : <strong className="text-white">{kpis.gravity_score}/10</strong></span>
            </div>
            <span className="bg-white/20 text-white text-[10px] font-bold px-3 py-1 rounded-full tracking-wider animate-pulse">LIVE</span>
          </div>
        </div>
      )}

      {/* === 4 KPIs — fond sombre, chiffres qui claquent === */}
      <div className="grid grid-cols-4 gap-3 mb-5">
        {/* Gravity Score */}
        <div className="bg-[#0f172a] rounded-2xl px-5 py-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-20 h-20 bg-red-500/10 rounded-full -translate-y-4 translate-x-4" />
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">Gravity Score</div>
          <div className="text-[42px] font-black text-red-500 leading-none tracking-tight">{kpis.gravity_score}<span className="text-[20px] text-red-400">/10</span></div>
          <div className="text-[11px] text-red-400 mt-1 font-medium">Action immédiate requise</div>
        </div>

        {/* Volume mentions */}
        <div className="bg-[#0f172a] rounded-2xl px-5 py-5">
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">Volume mentions</div>
          <div className="flex items-baseline gap-2">
            <span className="text-[36px] font-black text-white leading-none">{kpis.volume_total.toLocaleString('fr-FR')}</span>
            <span className="text-[12px] font-bold text-emerald-400">↑ +190% vs 7j</span>
          </div>
          <div className="text-[11px] text-gray-500 mt-1">toutes sources confondues</div>
        </div>

        {/* Sentiment négatif */}
        <div className="bg-[#0f172a] rounded-2xl px-5 py-5">
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">Sentiment négatif</div>
          <div className="text-[36px] font-black text-orange-400 leading-none">{Math.round(kpis.sentiment_negatif_pct * 100)}%</div>
          <div className="text-[11px] text-gray-500 mt-1">{Math.round(kpis.sentiment_negatif_pct * kpis.volume_total).toLocaleString('fr-FR')} mentions</div>
          {/* Mini bar */}
          <div className="h-1.5 bg-gray-800 rounded-full mt-2 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-orange-500 to-red-500 rounded-full" style={{ width: `${Math.round(kpis.sentiment_negatif_pct * 100)}%` }} />
          </div>
        </div>

        {/* CA menacé */}
        <div className="bg-[#0f172a] rounded-2xl px-5 py-5 relative overflow-hidden">
          <div className="absolute top-2 right-3 text-[20px]">⚠️</div>
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">CA menacé estimé</div>
          <div className="text-[36px] font-black text-red-500 leading-none">{caMenuce}M€</div>
          <div className="text-[11px] text-gray-500 mt-1">impact crise sur CA France</div>
        </div>
      </div>

      {/* === Timeline + Word Cloud — même ligne === */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">Volume & négatif — 14j</h3>
            {crisis?.is_escalating && (
              <span className="text-[10px] font-bold text-red-400 bg-red-50 px-2 py-0.5 rounded-full animate-pulse">EN HAUSSE</span>
            )}
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={timelineData} margin={{ top: 5, right: 5, left: -15, bottom: 0 }}>
              <defs>
                <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02}/>
                </linearGradient>
                <linearGradient id="colorNeg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                formatter={(value: number, name: string) => [value, name === 'volume' ? 'Volume' : 'Négatif']}
              />
              <Legend iconType="circle" iconSize={8} formatter={(v) => <span style={{ color: '#6b7280', fontSize: 11 }}>{v === 'volume' ? 'Volume' : 'Négatif'}</span>} />
              <Area type="monotone" dataKey="volume" stroke="#3b82f6" strokeWidth={2.5} fill="url(#colorVolume)" animationDuration={1000} />
              <Area type="monotone" dataKey="negative" stroke="#ef4444" strokeWidth={2.5} fill="url(#colorNeg)" animationDuration={1000} />
              {/* Peak annotation dot */}
              {crisis?.peak_day && (() => {
                const peakDate = crisis.peak_day.date.slice(5)
                const peakEntry = timelineData.find(d => d.date === peakDate)
                return peakEntry ? (
                  <ReferenceDot x={peakDate} y={peakEntry.volume} r={8} fill="#f59e0b" stroke="#fff" strokeWidth={2}>
                  </ReferenceDot>
                ) : null
              })()}
            </AreaChart>
          </ResponsiveContainer>
          {/* Peak info card */}
          {crisis?.peak_day && (
            <div className="mt-3 flex items-start gap-3 bg-amber-50 rounded-xl px-4 py-2.5 border border-amber-100">
              <span className="w-5 h-5 rounded-full bg-amber-400 text-white text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">A</span>
              <div className="text-[11px]">
                <span className="font-bold text-gray-800">{crisis.peak_day.date}</span>
                <span className="text-gray-500 ml-2">{crisis.peak_day.volume} mentions</span>
                <span className="text-amber-600 font-bold ml-2">+{Math.round((crisis.peak_day.volume / (crisis.avg_daily_volume || 1) - 1) * 100)}% vs moy.</span>
              </div>
            </div>
          )}
        </div>

        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <h3 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide mb-3">Thèmes dominants</h3>
          <WordCloud />
        </div>
      </div>

      {/* === Recommandation critique === */}
      <div className="bg-red-50 border-l-4 border-red-600 rounded-r-2xl px-6 py-5">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-red-600 text-[12px] font-black uppercase tracking-wider">Recommandation critique</span>
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
        </div>
        <p className="text-[14px] text-gray-800 leading-relaxed">
          <strong>Communiqué de crise vélo — 48h max.</strong> {kpis.volume_total.toLocaleString('fr-FR')} mentions dont {Math.round(kpis.sentiment_negatif_pct * 100)}% négatives.
          Publier un communiqué transparent + hotline dédiée.
        </p>
        <p className="text-[13px] text-emerald-600 font-bold mt-2">
          Impact estimé : -60% volume négatif en 7 jours.
        </p>
      </div>
    </div>
  )
}

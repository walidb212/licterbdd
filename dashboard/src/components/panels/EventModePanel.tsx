import { useState } from 'react'

const SCRAPERS = [
  { name: 'news_monitor', label: 'Google News', icon: '📰', status: 'ok', lastRun: '2026-04-07 18:32', items: 43 },
  { name: 'reddit_monitor', label: 'Reddit', icon: '🔴', status: 'ok', lastRun: '2026-04-07 18:33', items: 1006 },
  { name: 'instagram_monitor', label: 'Instagram', icon: '📸', status: 'ok', lastRun: '2026-04-07 18:35', items: 26 },
  { name: 'tiktok_monitor', label: 'TikTok', icon: '🎵', status: 'ok', lastRun: '2026-04-07 18:38', items: 76 },
  { name: 'youtube_monitor', label: 'YouTube', icon: '▶️', status: 'ok', lastRun: '2026-04-07 18:40', items: 175 },
  { name: 'x_monitor', label: 'X / Twitter', icon: '𝕏', status: 'ok', lastRun: '2026-04-07 22:48', items: 74 },
]

const LOGS = [
  { time: '18:40:12', msg: 'Cycle 1 terminé — 6 scrapers exécutés, 1 326 mentions collectées', type: 'success' },
  { time: '18:40:10', msg: 'youtube_monitor OK — 175 items', type: 'info' },
  { time: '18:38:45', msg: 'tiktok_monitor OK — 76 items (DrissionPage headless)', type: 'info' },
  { time: '18:35:22', msg: 'instagram_monitor OK — 26 items (GraphQL)', type: 'info' },
  { time: '18:33:15', msg: 'reddit_monitor OK — 1006 items (JSON API, 10s)', type: 'info' },
  { time: '18:32:08', msg: 'news_monitor OK — 43 articles', type: 'info' },
  { time: '22:48:59', msg: 'x_monitor OK – 74 tweets (Playwright login)', type: 'info' },
  { time: '18:32:00', msg: 'Event "Crise Vélo — Monitoring" démarré — interval 5min, auto-stop 2h', type: 'success' },
]

const HISTORY = [
  { name: 'Crise Vélo – Surveillance', date: '07/04/2026', cycles: 24, mentions: 1400, duration: '2h', status: 'completed' },
]

export default function EventModePanel() {
  const [isActive, setIsActive] = useState(false)
  const [eventName, setEventName] = useState('Crise Vélo — Monitoring')
  const [interval, setInterval_] = useState(5)

  return (
    <div>
      <div className="mb-5">
        <h2 className="text-base font-semibold text-[#324DE6] mb-1">Event Mode</h2>
        <p className="text-xs text-gray-400">Monitoring haute fréquence pendant les événements, crises ou lancements</p>
      </div>

      {/* Control Panel */}
      <div className={`rounded-xl p-5 mb-4 ${isActive ? 'bg-gradient-to-r from-red-50 to-orange-50 border border-red-200' : 'bg-white border border-gray-200 shadow-sm'}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {isActive && <span className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />}
            <span className={`text-[14px] font-bold ${isActive ? 'text-red-700' : 'text-gray-700'}`}>
              {isActive ? 'EVENT ACTIF' : 'Aucun event en cours'}
            </span>
            {isActive && <span className="text-[11px] text-gray-500">{eventName}</span>}
          </div>
          <button
            onClick={() => setIsActive(!isActive)}
            className={`px-5 py-2 rounded-xl text-[12px] font-bold transition-all ${isActive
              ? 'bg-red-600 text-white hover:bg-red-700'
              : 'bg-emerald-600 text-white hover:bg-emerald-700'}`}
          >
            {isActive ? 'Arrêter l\'event' : 'Démarrer un event'}
          </button>
        </div>

        {!isActive && (
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-[10px] text-gray-500 uppercase font-semibold block mb-1">Nom de l'event</label>
              <input value={eventName} onChange={e => setEventName(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 text-[12px] focus:outline-none focus:border-blue-400" />
            </div>
            <div>
              <label className="text-[10px] text-gray-500 uppercase font-semibold block mb-1">Intervalle (minutes)</label>
              <input type="number" value={interval} onChange={e => setInterval_(Number(e.target.value))} min={2} max={60}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 text-[12px] focus:outline-none focus:border-blue-400" />
            </div>
            <div>
              <label className="text-[10px] text-gray-500 uppercase font-semibold block mb-1">Scrapers actifs</label>
              <div className="text-[12px] text-gray-700 font-semibold mt-2">6 scrapers (news, reddit, instagram, tiktok, youtube, x)</div>
            </div>
          </div>
        )}

        {isActive && (
          <div className="grid grid-cols-4 gap-3">
            <div className="bg-white/80 rounded-lg p-3 text-center">
              <div className="text-[20px] font-black text-[#324DE6]">1</div>
              <div className="text-[9px] text-gray-400 uppercase">Cycles complétés</div>
            </div>
            <div className="bg-white/80 rounded-lg p-3 text-center">
              <div className="text-[20px] font-black text-emerald-600">1 326</div>
              <div className="text-[9px] text-gray-400 uppercase">Mentions collectées</div>
            </div>
            <div className="bg-white/80 rounded-lg p-3 text-center">
              <div className="text-[20px] font-black text-amber-600">5 min</div>
              <div className="text-[9px] text-gray-400 uppercase">Intervalle</div>
            </div>
            <div className="bg-white/80 rounded-lg p-3 text-center">
              <div className="text-[20px] font-black text-gray-700">18:45</div>
              <div className="text-[9px] text-gray-400 uppercase">Prochain scrape</div>
            </div>
          </div>
        )}
      </div>

      {/* Scrapers Status + Logs */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {/* Scrapers */}
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-3">Statut des scrapers</h3>
          <div className="space-y-2">
            {SCRAPERS.map((s, i) => (
              <div key={i} className="flex items-center gap-3 py-1.5 border-b border-gray-50 last:border-0">
                <span className="text-[14px] w-6 text-center">{s.icon}</span>
                <span className="text-[12px] font-medium text-gray-700 flex-1">{s.label}</span>
                <span className="text-[10px] text-gray-400">{s.items > 0 ? `${s.items} items` : '—'}</span>
                <span className={`w-2 h-2 rounded-full ${s.status === 'ok' ? 'bg-emerald-500' : 'bg-red-400'}`} />
              </div>
            ))}
          </div>
        </div>

        {/* Logs */}
        <div className="bg-[#1a1a2e] rounded-xl p-4 shadow-sm">
          <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-3">Logs en temps réel</h3>
          <div className="space-y-1.5 font-mono">
            {LOGS.map((l, i) => (
              <div key={i} className="text-[10px] leading-relaxed">
                <span className="text-gray-500">[{l.time}]</span>{' '}
                <span className={l.type === 'error' ? 'text-red-400' : l.type === 'success' ? 'text-emerald-400' : 'text-gray-300'}>{l.msg}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* How it works */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-[#324DE6] rounded-r-xl px-4 py-3 mb-4">
        <p className="text-[12px] text-gray-700 leading-relaxed">
          <strong className="text-[#324DE6]">Comment ça marche :</strong> L'Event Mode lance tous les scrapers sociaux (news, reddit, instagram, tiktok, youtube, x)
          toutes les N minutes. Les données sont réingérées dans la base, les KPIs recalculés, et les alertes envoyées automatiquement si les seuils sont dépassés
          (Gravity Score &gt; 7, Sentiment négatif &gt; 70%, Volume &gt; 2× moyenne).
        </p>
      </div>

      {/* History */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-3">Historique des events</h3>
        <table className="w-full text-[11px]">
          <thead>
            <tr className="text-[9px] text-gray-400 uppercase">
              <th className="text-left pb-2">Event</th>
              <th className="text-left pb-2">Date</th>
              <th className="text-right pb-2">Cycles</th>
              <th className="text-right pb-2">Mentions</th>
              <th className="text-right pb-2">Durée</th>
              <th className="text-center pb-2">Statut</th>
            </tr>
          </thead>
          <tbody>
            {HISTORY.map((h, i) => (
              <tr key={i} className="border-t border-gray-50">
                <td className="py-2 font-semibold text-gray-700">{h.name}</td>
                <td className="py-2 text-gray-500">{h.date}</td>
                <td className="py-2 text-right font-bold">{h.cycles}</td>
                <td className="py-2 text-right font-bold text-[#324DE6]">{h.mentions.toLocaleString('fr-FR')}</td>
                <td className="py-2 text-right text-gray-500">{h.duration}</td>
                <td className="py-2 text-center"><span className="text-[9px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-bold">Terminé</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

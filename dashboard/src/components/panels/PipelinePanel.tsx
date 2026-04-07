import { useState } from 'react'

const TRANSCRIPTS = [
  { source: 'YouTube', title: 'Vélo Rockrider défectueux — témoignage client', duration: '4:32', provider: 'Groq Whisper', lang: 'fr', excerpt: 'J\'ai acheté un Rockrider 520 il y a 3 mois. Au bout de 2 semaines, le dérailleur s\'est cassé en pleine descente. J\'ai failli avoir un accident grave...', sentiment: 'negative', views: '178k' },
  { source: 'TikTok', title: 'Ceinture hydratation Decathlon — test terrain', duration: '1:15', provider: 'Groq Whisper', lang: 'fr', excerpt: 'Franchement la ceinture hydratation Kalenji c\'est le meilleur rapport qualité prix que j\'ai trouvé. Elle bouge pas du tout pendant la course...', sentiment: 'positive', views: '3.1M' },
  { source: 'YouTube', title: 'Decathlon vs Intersport — comparatif running 2026', duration: '12:08', provider: 'YouTube Auto-sub', lang: 'fr', excerpt: 'On a testé les mêmes catégories chez les deux enseignes. Sur le running, Decathlon gagne clairement avec Kiprun. Mais Intersport a l\'avantage sur les grandes marques...', sentiment: 'neutral', views: '45k' },
  { source: 'YouTube', title: 'Transition Vélo — review complète Riverside', duration: '8:45', provider: 'YouTube Auto-sub', lang: 'fr', excerpt: 'Le Riverside 500 est un excellent vélo pour débuter le gravel. Cadre alu solide, freins à disque hydrauliques, et surtout un prix imbattable à 549€...', sentiment: 'positive', views: '178k' },
]

const TRENDS = [
  { trend: 'Rucking', spike: '+240%', volume: 34, categories: ['Fitness', 'Outdoor'], platforms: ['Reddit', 'YouTube', 'TikTok'], priority: 'high', opportunity: 'Marche avec sac lesté — tendance US qui explose en France. Decathlon peut lancer un sac dédié sous Domyos.' },
  { trend: 'Padel', spike: '+180%', volume: 28, categories: ['Raquettes', 'Sport collectif'], platforms: ['TikTok', 'Instagram'], priority: 'high', opportunity: 'Sport en forte croissance. Intersport a déjà des packs. Decathlon doit accélérer sur l\'équipement entrée de gamme.' },
  { trend: 'Gravel Bikepacking', spike: '+120%', volume: 19, categories: ['Vélo', 'Outdoor'], platforms: ['YouTube', 'Reddit'], priority: 'medium', opportunity: 'Niche en croissance. Le Riverside est bien positionné mais manque d\'accessoires bikepacking (sacoches, racks).' },
  { trend: 'Cold Plunge', spike: '+95%', volume: 12, categories: ['Récupération', 'Fitness'], platforms: ['TikTok', 'YouTube'], priority: 'medium', opportunity: 'Bains froids post-entraînement. Accessoires récupération (serviettes, thermomètres, bacs) = extension catalogue Decathlon.' },
  { trend: 'Hyrox Training', spike: '+85%', volume: 15, categories: ['Fitness', 'Running'], platforms: ['Instagram', 'YouTube'], priority: 'low', opportunity: 'Compétitions fitness/running hybrides. Decathlon peut sponsoriser des events locaux.' },
]

const DISCOVERIES = [
  { type: 'subreddit', name: 'r/ultrarunning', mentions: 12, relevance: 'high', action: 'Ajouter à reddit_monitor — communauté active trail/ultra' },
  { type: 'subreddit', name: 'r/gravelcycling', mentions: 8, relevance: 'high', action: 'Ajouter à reddit_monitor — niche vélo en croissance' },
  { type: 'hashtag', name: '#decathlonhack', mentions: 23, relevance: 'high', action: 'Ajouter à tiktok_monitor — détournements produits viraux' },
  { type: 'hashtag', name: '#sportpascher', mentions: 15, relevance: 'medium', action: 'Déjà monitoré TikTok — étendre à Instagram' },
  { type: 'account', name: '@staborowski_', mentions: 6, relevance: 'medium', action: 'Influenceur trail 45k followers — mentionner dans watch list' },
  { type: 'forum', name: 'Que Choisir Sport', mentions: 9, relevance: 'high', action: 'Ajouter à review_monitor — avis consommateurs indépendants' },
]

const PRIORITY_COLORS = { high: 'bg-red-100 text-red-700', medium: 'bg-amber-100 text-amber-700', low: 'bg-blue-100 text-blue-700' }
const SENT_COLORS = { positive: 'text-green-600', negative: 'text-red-600', neutral: 'text-gray-500' }
const TYPE_ICONS = { subreddit: '🔴', hashtag: '#', account: '👤', forum: '💬' }

export default function PipelinePanel() {
  const [tab, setTab] = useState<'transcripts' | 'trending' | 'discovery'>('transcripts')

  return (
    <div>
      <div className="mb-5">
        <h2 className="text-base font-semibold text-[#324DE6] mb-1">Pipeline Intelligence</h2>
        <p className="text-xs text-gray-400">Transcription vidéo, détection de tendances et découverte automatique de sources</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        {[
          { id: 'transcripts' as const, label: 'Transcripts Vidéo', icon: '🎙', count: TRANSCRIPTS.length },
          { id: 'trending' as const, label: 'Trending Opportunities', icon: '📈', count: TRENDS.length },
          { id: 'discovery' as const, label: 'Auto-Discovery', icon: '🔍', count: DISCOVERIES.length },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-xl text-[12px] font-semibold transition-all flex items-center gap-2 ${tab === t.id ? 'bg-[#324DE6] text-white shadow-md' : 'bg-white text-gray-500 border border-gray-200 hover:border-gray-300'}`}>
            <span>{t.icon}</span> {t.label}
            <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${tab === t.id ? 'bg-white/20' : 'bg-gray-100'}`}>{t.count}</span>
          </button>
        ))}
      </div>

      {/* Transcripts */}
      {tab === 'transcripts' && (
        <div>
          <div className="grid grid-cols-3 gap-2 mb-4">
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 text-center">
              <div className="text-[22px] font-black text-[#324DE6]">{TRANSCRIPTS.length}</div>
              <div className="text-[10px] text-gray-400 uppercase">Vidéos transcrites</div>
            </div>
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 text-center">
              <div className="text-[22px] font-black text-purple-600">Groq Whisper</div>
              <div className="text-[10px] text-gray-400 uppercase">Provider principal (gratuit)</div>
            </div>
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 text-center">
              <div className="text-[22px] font-black text-gray-700">FR</div>
              <div className="text-[10px] text-gray-400 uppercase">Langue détectée</div>
            </div>
          </div>

          <div className="space-y-3">
            {TRANSCRIPTS.map((t, i) => (
              <div key={i} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 font-bold">{t.source}</span>
                    <span className="text-[13px] font-semibold text-gray-800">{t.title}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-gray-400">{t.duration}</span>
                    <span className="text-[10px] text-gray-400">{t.views} vues</span>
                    <span className={`text-[10px] font-bold ${SENT_COLORS[t.sentiment]}`}>{t.sentiment === 'positive' ? '😊' : t.sentiment === 'negative' ? '😠' : '😐'}</span>
                  </div>
                </div>
                <p className="text-[12px] text-gray-600 italic leading-relaxed bg-gray-50 rounded-lg p-3">"{t.excerpt}"</p>
                <div className="flex items-center gap-3 mt-2 text-[10px] text-gray-400">
                  <span>Provider : <strong className="text-purple-600">{t.provider}</strong></span>
                  <span>Langue : {t.lang}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trending */}
      {tab === 'trending' && (
        <div>
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-l-4 border-[#324DE6] rounded-r-xl px-4 py-3 mb-4">
            <p className="text-[12px] text-gray-700">
              <strong className="text-[#324DE6]">Comment ça marche :</strong> On scanne les hashtags, thèmes et topics de toutes les mentions sociales.
              On détecte les sujets en hausse liés au sport que Decathlon pourrait exploiter commercialement.
            </p>
          </div>

          <div className="space-y-3">
            {TRENDS.map((t, i) => (
              <div key={i} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[16px] font-black text-gray-800">{t.trend}</span>
                    <span className="text-[12px] font-bold text-emerald-600">{t.spike}</span>
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${PRIORITY_COLORS[t.priority]}`}>{t.priority.toUpperCase()}</span>
                  </div>
                  <span className="text-[11px] text-gray-400">{t.volume} mentions</span>
                </div>
                <p className="text-[12px] text-gray-600 leading-relaxed mb-2">{t.opportunity}</p>
                <div className="flex items-center gap-2">
                  {t.categories.map((c, j) => (
                    <span key={j} className="text-[9px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 font-semibold">{c}</span>
                  ))}
                  <span className="text-[9px] text-gray-400 ml-auto">{t.platforms.join(' • ')}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Auto-Discovery */}
      {tab === 'discovery' && (
        <div>
          <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-l-4 border-amber-500 rounded-r-xl px-4 py-3 mb-4">
            <p className="text-[12px] text-gray-700">
              <strong className="text-amber-700">Comment ça marche :</strong> On scanne tous les textes collectés (social, avis, presse) pour détecter
              des subreddits, hashtags, comptes et forums que nos scrapers ne surveillent pas encore.
            </p>
          </div>

          <div className="grid grid-cols-4 gap-2 mb-4">
            <div className="bg-white rounded-xl p-3 shadow-sm border border-gray-100 text-center">
              <div className="text-[20px] font-black text-gray-800">8 156</div>
              <div className="text-[9px] text-gray-400 uppercase">Textes scannés</div>
            </div>
            <div className="bg-white rounded-xl p-3 shadow-sm border border-gray-100 text-center">
              <div className="text-[20px] font-black text-red-600">2</div>
              <div className="text-[9px] text-gray-400 uppercase">Subreddits trouvés</div>
            </div>
            <div className="bg-white rounded-xl p-3 shadow-sm border border-gray-100 text-center">
              <div className="text-[20px] font-black text-purple-600">2</div>
              <div className="text-[9px] text-gray-400 uppercase">Hashtags trouvés</div>
            </div>
            <div className="bg-white rounded-xl p-3 shadow-sm border border-gray-100 text-center">
              <div className="text-[20px] font-black text-blue-600">2</div>
              <div className="text-[9px] text-gray-400 uppercase">Comptes / Forums</div>
            </div>
          </div>

          <div className="space-y-2">
            {DISCOVERIES.map((d, i) => (
              <div key={i} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 flex items-center gap-4">
                <span className="text-[18px] w-8 text-center">{TYPE_ICONS[d.type] || '📌'}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[13px] font-bold text-gray-800">{d.name}</span>
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${d.relevance === 'high' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>{d.relevance}</span>
                    <span className="text-[10px] text-gray-400">{d.mentions} mentions dans nos données</span>
                  </div>
                  <p className="text-[11px] text-gray-500">{d.action}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

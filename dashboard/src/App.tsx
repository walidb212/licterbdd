import { useState } from 'react'
import ReputationPanel from './components/panels/ReputationPanel'
import BenchmarkPanel from './components/panels/BenchmarkPanel'
import CxPanel from './components/panels/CxPanel'
import RecoPanel from './components/panels/RecoPanel'
import SynthesePanel from './components/panels/SynthesePanel'
import PersonasPanel from './components/panels/PersonasPanel'
import ChatPanel from './components/panels/ChatPanel'
import HeatmapPanel from './components/panels/HeatmapPanel'
import InfluencersPanel from './components/panels/InfluencersPanel'
import ContentComparePanel from './components/panels/ContentComparePanel'
import AdminDbPanel from './components/panels/AdminDbPanel'
import TranscriptsPanel from './components/panels/TranscriptsPanel'
import { useHealth } from './api/client'

type NavId = 'rep' | 'bench' | 'cx' | 'reco' | 'synthese' | 'personas' | 'heatmap' | 'influencers' | 'content' | 'admindb' | 'transcripts'

const NAV_ITEMS: { id: NavId; label: string; icon: string; section: string }[] = [
  { id: 'rep', label: 'Réputation', icon: '🛡', section: 'GENERAL' },
  { id: 'bench', label: 'Benchmark', icon: '⚔', section: 'GENERAL' },
  { id: 'cx', label: 'Expérience Client', icon: '★', section: 'GENERAL' },
  { id: 'reco', label: 'Recommandations', icon: '◎', section: 'GENERAL' },
  { id: 'heatmap', label: 'Carte Sentiment', icon: '📍', section: 'TOOLS' },
  { id: 'influencers', label: 'Influenceurs', icon: '👥', section: 'TOOLS' },
  { id: 'content', label: 'Comparateur IA', icon: '⚡', section: 'TOOLS' },
  { id: 'transcripts', label: 'Transcripts', icon: '🎙', section: 'TOOLS' },
  { id: 'synthese', label: 'Synthèse IA', icon: '◈', section: 'TOOLS' },
  { id: 'personas', label: 'Personas', icon: '♟', section: 'TOOLS' },
  { id: 'admindb', label: 'Admin DB', icon: '🗄', section: 'TOOLS' },
]

function App() {
  const [activeNav, setActiveNav] = useState<NavId>('rep')
  const [chatOpen, setChatOpen] = useState(false)
  const { data: health } = useHealth()

  const generalItems = NAV_ITEMS.filter(i => i.section === 'GENERAL')
  const toolItems = NAV_ITEMS.filter(i => i.section === 'TOOLS')

  return (
    <div className="flex h-screen bg-[#1a1a2e] p-3 gap-3">
      {/* ── Sidebar ── */}
      <aside className="w-[230px] bg-white rounded-[20px] flex flex-col shrink-0 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-2">
          <img src="/decathlon.png?v=5" alt="Decathlon" className="w-[150px] h-auto object-contain" />
        </div>

        {/* General nav */}
        <div className="px-4 mb-1 text-[10px] font-semibold text-[#324DE6] tracking-wider">GENERAL</div>
        <nav className="px-2 flex flex-col gap-0.5">
          {generalItems.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveNav(item.id)}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] w-full text-left transition-all
                ${activeNav === item.id
                  ? 'bg-white text-gray-900 font-semibold shadow-sm'
                  : 'text-gray-500 hover:bg-white/60 hover:text-gray-700'}`}
            >
              <span className="w-5 text-center text-sm">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        {/* Tools nav */}
        <div className="px-4 mt-6 mb-1 text-[10px] font-semibold text-[#324DE6] tracking-wider">TOOLS</div>
        <nav className="px-2 flex flex-col gap-0.5">
          {toolItems.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveNav(item.id)}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] w-full text-left transition-all
                ${activeNav === item.id
                  ? 'bg-white text-gray-900 font-semibold shadow-sm'
                  : 'text-gray-500 hover:bg-white/60 hover:text-gray-700'}`}
            >
              <span className="w-5 text-center text-sm">{item.icon}</span>
              {item.label}
            </button>
          ))}
          <a href="/rapport-comex.pdf" target="_blank"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] text-gray-500 hover:bg-white/60 hover:text-gray-700 no-underline transition-all">
            <span className="w-5 text-center text-sm">⬡</span>
            Rapport PDF
          </a>
        </nav>

        {/* Footer */}
        <div className="mt-auto px-4 py-4 border-t border-gray-100">
          {health?.status === 'ok' && (
            <div className="flex items-center gap-2 text-[11px] text-green-600 mb-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse-dot" />
              Pipeline actif
            </div>
          )}
          <div className="text-[10px] text-gray-400">LICTER v1.0 — Mars 2026</div>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex-1 min-w-0 flex flex-col bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] overflow-hidden" data-theme="light" style={{ colorScheme: 'light' }}>
        {/* Header */}
        <header className="px-7 py-5 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-[#324DE6]">
              {NAV_ITEMS.find(n => n.id === activeNav)?.label}
            </h1>
            <p className="text-[11px] text-gray-400 mt-0.5">Dashboard COMEX — Matrice de Bataille</p>
          </div>
          <div className="flex items-center gap-2">
            <a href="/rapport-comex.pdf" target="_blank"
              className="px-4 py-1.5 rounded-full text-[12px] font-bold border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-300 no-underline transition-all flex items-center gap-2 shadow-sm">
              Rapport PDF <span className="opacity-40">↓</span>
            </a>
            <a href="/licter-export.csv" download="licter-export.csv"
              className="px-4 py-1.5 rounded-full text-[12px] font-bold border border-green-200 bg-green-50 text-green-700 hover:bg-green-100 hover:border-green-300 no-underline transition-all flex items-center gap-2 shadow-sm">
              Export Excel <span className="opacity-40">↓</span>
            </a>
          </div>
        </header>

        {/* Content scroll */}
        <div className="main-scroll flex-1 overflow-y-auto p-7 bg-[#f5f6f8]">
          {activeNav === 'rep' && <ReputationPanel />}
          {activeNav === 'bench' && <BenchmarkPanel />}
          {activeNav === 'cx' && <CxPanel />}
          {activeNav === 'reco' && <RecoPanel />}
          {activeNav === 'heatmap' && <HeatmapPanel />}
          {activeNav === 'influencers' && <InfluencersPanel />}
          {activeNav === 'content' && <ContentComparePanel />}
          {activeNav === 'transcripts' && <TranscriptsPanel />}
          {activeNav === 'synthese' && <SynthesePanel />}
          {activeNav === 'personas' && <PersonasPanel />}
          {activeNav === 'admindb' && <AdminDbPanel />}
        </div>
      </main>

      {/* ── Chat Floating Bubble ── */}
      <div className="fixed bottom-8 right-8 flex flex-col items-end gap-3 z-50">
        {chatOpen && (
          <aside className="w-[400px] h-[620px] bg-white rounded-[24px] shadow-[0_20px_50px_rgba(0,0,0,0.15)] flex flex-col overflow-hidden border border-gray-100 animate-slide-up">
            <div className="flex items-center justify-between px-5 py-4 bg-decathlon">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg overflow-hidden border border-white/20">
                  <img src="/ai-logo.jpg" alt="AI Agent" className="w-full h-full object-cover" />
                </div>
                <div>
                  <div className="text-sm font-bold text-white">Assistant Brand Intelligence</div>
                  <div className="text-[10px] text-white/70">Agent IA • Session active</div>
                </div>
              </div>
              <button
                onClick={() => setChatOpen(false)}
                className="text-white/60 hover:text-white hover:bg-white/10 rounded-full p-1.5 transition-all outline-none"
              >
                <span className="text-sm block leading-none">✕</span>
              </button>
            </div>
            <div className="flex-1 overflow-hidden flex flex-col">
              <ChatPanel />
            </div>
          </aside>
        )}
        
        <button
          onClick={() => setChatOpen(!chatOpen)}
          className={`w-[52px] h-[52px] rounded-full overflow-hidden flex items-center justify-center shadow-xl transition-all duration-300 hover:scale-110 active:scale-95 border-2
            ${chatOpen 
              ? 'bg-white text-decathlon border-decathlon shadow-decathlon/20' 
              : 'bg-decathlon border-transparent text-white hover:shadow-decathlon/40'}`}
        >
          {chatOpen ? (
            <span className="text-xl font-bold">✕</span>
          ) : (
            <div className="relative w-full h-full">
              <img src="/ai-logo.jpg" alt="AI" className="w-full h-full object-cover" />
            </div>
          )}
        </button>
      </div>
    </div>
  )
}

export default App

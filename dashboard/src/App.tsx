import { useState } from 'react'
import ReputationPanel from './components/panels/ReputationPanel'
import BenchmarkPanel from './components/panels/BenchmarkPanel'
import CxPanel from './components/panels/CxPanel'
import RecoPanel from './components/panels/RecoPanel'
import SynthesePanel from './components/panels/SynthesePanel'
import PersonasPanel from './components/panels/PersonasPanel'
import ChatPanel from './components/panels/ChatPanel'
import { useHealth } from './api/client'

type NavId = 'rep' | 'bench' | 'cx' | 'reco' | 'synthese' | 'personas'

const NAV_ITEMS: { id: NavId; label: string; icon: string; section: string }[] = [
  { id: 'rep',      label: 'Réputation',        icon: '🛡', section: 'GENERAL' },
  { id: 'bench',    label: 'Benchmark',         icon: '⚔',  section: 'GENERAL' },
  { id: 'cx',       label: 'Expérience Client', icon: '★',  section: 'GENERAL' },
  { id: 'reco',     label: 'Recommandations',   icon: '◎',  section: 'GENERAL' },
  { id: 'synthese', label: 'Synthèse IA',       icon: '◈',  section: 'TOOLS' },
  { id: 'personas', label: 'Personas',          icon: '♟',  section: 'TOOLS' },
]

function App() {
  const [activeNav, setActiveNav] = useState<NavId>('rep')
  const [chatOpen, setChatOpen] = useState(true)
  const { data: health } = useHealth()

  const generalItems = NAV_ITEMS.filter(i => i.section === 'GENERAL')
  const toolItems = NAV_ITEMS.filter(i => i.section === 'TOOLS')

  return (
    <div className="flex h-screen bg-[#1a1a2e] p-3 gap-3">
      {/* ── Sidebar ── */}
      <aside className="w-[230px] bg-white rounded-[20px] flex flex-col shrink-0 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 pt-5 pb-6">
          <div className="w-9 h-9 rounded-xl bg-green-800 text-white flex items-center justify-center font-extrabold text-sm">L</div>
          <div>
            <div className="text-[15px] font-bold text-gray-900">LICTER</div>
            <div className="text-[10px] text-gray-400">× Decathlon</div>
          </div>
        </div>

        {/* General nav */}
        <div className="px-4 mb-1 text-[10px] font-semibold text-gray-400 tracking-wider">GENERAL</div>
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
        <div className="px-4 mt-6 mb-1 text-[10px] font-semibold text-gray-400 tracking-wider">TOOLS</div>
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
          <button
            onClick={() => setChatOpen(!chatOpen)}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] w-full text-left transition-all
              ${chatOpen ? 'bg-gray-100 text-gray-900 font-semibold' : 'text-gray-500 hover:bg-gray-50'}`}
          >
            <span className="w-5 text-center text-sm">◉</span>
            Assistant IA
          </button>
          <a href="/api/report/pdf" target="_blank"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] text-gray-500 hover:bg-gray-50 hover:text-gray-700 no-underline transition-all">
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
            <h1 className="text-xl font-bold text-gray-900">
              {NAV_ITEMS.find(n => n.id === activeNav)?.label}
            </h1>
            <p className="text-[11px] text-gray-400 mt-0.5">Dashboard COMEX — Matrice de Bataille</p>
          </div>
          <div className="flex items-center gap-2 bg-gray-100 rounded-full p-1">
            <a href="/api/report/html" target="_blank"
              className="px-4 py-1.5 rounded-full text-[12px] font-medium text-gray-500 hover:bg-white hover:shadow-sm no-underline transition-all">
              Aperçu
            </a>
            <a href="/api/report/pdf" target="_blank"
              className="px-4 py-1.5 rounded-full text-[12px] font-medium bg-gray-800 text-white hover:bg-gray-700 no-underline transition-all">
              PDF
            </a>
          </div>
        </header>

        {/* Content scroll */}
        <div className="main-scroll flex-1 overflow-y-auto p-7 bg-[#f5f6f8]">
          {activeNav === 'rep'      && <ReputationPanel />}
          {activeNav === 'bench'    && <BenchmarkPanel />}
          {activeNav === 'cx'       && <CxPanel />}
          {activeNav === 'reco'     && <RecoPanel />}
          {activeNav === 'synthese' && <SynthesePanel />}
          {activeNav === 'personas' && <PersonasPanel />}
        </div>
      </main>

      {/* ── Chat sidebar (right) ── */}
      {chatOpen && (
        <aside className="w-[380px] bg-white rounded-[20px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] flex flex-col shrink-0 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <span className="text-sm font-bold text-gray-900">Assistant IA</span>
            <button
              onClick={() => setChatOpen(false)}
              className="text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md p-1 transition-all text-sm"
            >✕</button>
          </div>
          <ChatPanel />
        </aside>
      )}
    </div>
  )
}

export default App

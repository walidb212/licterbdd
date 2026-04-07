import { useState } from 'react'
import ReputationPanel from './components/panels/ReputationPanel'
import BenchmarkPanel from './components/panels/BenchmarkPanel'
import CxPanel from './components/panels/CxPanel'
import RecoPanel from './components/panels/RecoPanel'
import ChatPanel from './components/panels/ChatPanel'
import ContentComparePanel from './components/panels/ContentComparePanel'
import AdminDbPanel from './components/panels/AdminDbPanel'
import LlmVisibilityPanel from './components/panels/LlmVisibilityPanel'
import SwotPanel from './components/panels/SwotPanel'
import PipelinePanel from './components/panels/PipelinePanel'
import EventModePanel from './components/panels/EventModePanel'
import { useHealth } from './api/client'

type NavId = 'rep' | 'bench' | 'cx' | 'reco' | 'swot' | 'llmvis' | 'pipeline' | 'eventmode' | 'content' | 'admindb'

const NAV_ITEMS: { id: NavId; label: string; icon: string; section: string }[] = [
  { id: 'rep', label: 'Réputation', icon: '🛡', section: 'GENERAL' },
  { id: 'bench', label: 'Benchmark', icon: '⚔', section: 'GENERAL' },
  { id: 'cx', label: 'Expérience Client', icon: '★', section: 'GENERAL' },
  { id: 'reco', label: 'Recommandations', icon: '◎', section: 'GENERAL' },
  { id: 'swot', label: 'SWOT', icon: '⊞', section: 'TOOLS' },
  { id: 'llmvis', label: 'LLM Visibility', icon: '🤖', section: 'TOOLS' },
  { id: 'pipeline', label: 'Pipeline IA', icon: '⚙', section: 'TOOLS' },
  { id: 'eventmode', label: 'Event Mode', icon: '⚡', section: 'TOOLS' },
  { id: 'content', label: 'Comparateur IA', icon: '⚡', section: 'TOOLS' },
  { id: 'admindb', label: 'Admin DB', icon: '🗄', section: 'TOOLS' },
]

function App() {
  const [activeNav, setActiveNav] = useState<NavId>('rep')
  const [chatOpen, setChatOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [toolsOpen, setToolsOpen] = useState(false)
  const { data: health } = useHealth()

  const generalItems = NAV_ITEMS.filter(i => i.section === 'GENERAL')
  const toolItems = NAV_ITEMS.filter(i => i.section === 'TOOLS')

  return (
    <div className="flex h-screen bg-[#1a1a2e] p-3 gap-3">
      {/* ── Sidebar ── */}
      <aside className={`${sidebarOpen ? 'w-[230px]' : 'w-[60px]'} bg-white rounded-[20px] flex flex-col shrink-0 shadow-[0_2px_8px_rgba(0,0,0,0.06)] transition-all duration-300 overflow-y-auto overflow-x-hidden`}>
        {/* Logo + collapse toggle */}
        <div className="flex items-center justify-between px-3 py-2">
          {sidebarOpen && <img src="/decathlon.png?v=5" alt="Decathlon" className="w-[130px] h-auto object-contain" />}
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-all shrink-0">
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>

        {/* General nav */}
        {sidebarOpen && <div className="px-4 mb-1 text-[10px] font-semibold text-[#324DE6] tracking-wider">GENERAL</div>}
        <nav className="px-2 flex flex-col gap-0.5">
          {generalItems.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveNav(item.id)}
              title={item.label}
              className={`flex items-center gap-3 ${sidebarOpen ? 'px-3' : 'px-0 justify-center'} py-2 rounded-lg text-[13px] w-full text-left transition-all
                ${activeNav === item.id
                  ? 'bg-white text-gray-900 font-semibold shadow-sm'
                  : 'text-gray-500 hover:bg-white/60 hover:text-gray-700'}`}
            >
              <span className="w-5 text-center text-sm shrink-0">{item.icon}</span>
              {sidebarOpen && item.label}
            </button>
          ))}
        </nav>

        {/* Tools nav */}
        {sidebarOpen ? (
          <button onClick={() => setToolsOpen(!toolsOpen)} className="px-4 mt-5 mb-1 text-[10px] font-semibold text-[#324DE6] tracking-wider flex items-center gap-1 w-full hover:opacity-70 transition-opacity">
            <span className="text-[8px]">{toolsOpen ? '▼' : '▶'}</span> OUTILS AVANCÉS ({toolItems.length})
          </button>
        ) : (
          <button onClick={() => setToolsOpen(!toolsOpen)} className="px-2 mt-4 mb-1 w-full flex justify-center">
            <span className="text-[10px] text-[#324DE6]">{toolsOpen ? '▼' : '▶'}</span>
          </button>
        )}
        {toolsOpen && (
          <nav className="px-2 flex flex-col gap-0.5">
            {toolItems.map(item => (
              <button
                key={item.id}
                onClick={() => setActiveNav(item.id)}
                title={item.label}
                className={`flex items-center gap-3 ${sidebarOpen ? 'px-3' : 'px-0 justify-center'} py-1.5 rounded-lg text-[12px] w-full text-left transition-all
                  ${activeNav === item.id
                    ? 'bg-white text-gray-900 font-semibold shadow-sm'
                    : 'text-gray-400 hover:bg-white/60 hover:text-gray-600'}`}
              >
                <span className="w-5 text-center text-sm shrink-0">{item.icon}</span>
                {sidebarOpen && item.label}
              </button>
            ))}
          </nav>
        )}

        {/* Status indicator only */}
        {health?.status === 'ok' && (
          <div className={`mt-auto ${sidebarOpen ? 'px-4' : 'px-2'} py-3`}>
            <div className={`flex items-center gap-2 text-[11px] text-green-600 ${sidebarOpen ? '' : 'justify-center'}`}>
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse-dot shrink-0" />
              {sidebarOpen && 'Pipeline actif'}
            </div>
          </div>
        )}
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
          {activeNav === 'swot' && <SwotPanel />}
          {activeNav === 'llmvis' && <LlmVisibilityPanel />}
          {activeNav === 'pipeline' && <PipelinePanel />}
          {activeNav === 'eventmode' && <EventModePanel />}
          {activeNav === 'content' && <ContentComparePanel />}
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

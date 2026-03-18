import { useState } from 'react'
import TabBar from './components/TabBar'
import type { TabId } from './components/TabBar'
import ReputationPanel from './components/panels/ReputationPanel'
import BenchmarkPanel from './components/panels/BenchmarkPanel'
import CxPanel from './components/panels/CxPanel'
import RecoPanel from './components/panels/RecoPanel'
import SynthesePanel from './components/panels/SynthesePanel'
import { useHealth } from './api/client'

function App() {
  const [activeTab, setActiveTab] = useState<TabId>('rep')
  const { data: health } = useHealth()

  return (
    <>
      <header className="app-header">
        <div className="app-header__logo">
          LICTER <span>×</span> Decathlon
        </div>
        <div className="app-header__subtitle">
          Dashboard COMEX — Matrice de Bataille — Mars 2026
          {health?.label && (
            <span style={{ marginLeft: 16, fontSize: 11, color: 'var(--color-text-tertiary)', fontWeight: 400 }}>
              · Données au {health.label}
            </span>
          )}
        </div>
      </header>

      <TabBar active={activeTab} onChange={setActiveTab} />

      <main className="app-content">
        {activeTab === 'rep'      && <ReputationPanel />}
        {activeTab === 'bench'    && <BenchmarkPanel />}
        {activeTab === 'cx'       && <CxPanel />}
        {activeTab === 'reco'     && <RecoPanel />}
        {activeTab === 'synthese' && <SynthesePanel />}
      </main>
    </>
  )
}

export default App

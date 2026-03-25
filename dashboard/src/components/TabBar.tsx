export type TabId = 'rep' | 'bench' | 'cx' | 'reco' | 'synthese' | 'chat'

const TABS: { id: TabId; label: string }[] = [
  { id: 'rep',      label: 'Réputation' },
  { id: 'bench',    label: 'Benchmark' },
  { id: 'cx',       label: 'Expérience Client' },
  { id: 'reco',     label: 'Recommandations' },
  { id: 'synthese', label: 'Synthèse IA' },
  { id: 'chat',     label: 'Assistant IA' },
]

interface TabBarProps {
  active: TabId
  onChange: (tab: TabId) => void
}

export default function TabBar({ active, onChange }: TabBarProps) {
  return (
    <nav className="tab-bar">
      {TABS.map(t => (
        <button
          key={t.id}
          className={`tab-bar__item${active === t.id ? ' tab-bar__item--active' : ''}`}
          onClick={() => onChange(t.id)}
        >
          {t.label}
        </button>
      ))}
    </nav>
  )
}

import { useQuery } from '@tanstack/react-query'

interface Persona {
  name: string
  age: number
  profile: string
  motivations: string[]
  frustrations: string[]
  channels: string[]
  satisfaction_score: number
  recommendation: string
}

export default function PersonasPanel() {
  const { data, isLoading, error } = useQuery<{ personas: Persona[] }>({
    queryKey: ['personas'],
    queryFn: () => fetch('/api/personas').then(r => r.json()),
    staleTime: 1800_000,
  })

  if (isLoading) return <div className="loading">Génération des personas via IA...</div>
  if (error) return <div className="error-msg">Erreur : {(error as Error).message}</div>

  const personas = data?.personas || []

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">Personas Consommateurs</h2>
        <p className="section-subtitle">Profils synthétiques générés par IA à partir des verbatims clients</p>
      </div>
      <div className="personas-grid">
        {personas.map((p, i) => (
          <div key={i} className="persona-card">
            <div className="persona-card__header">
              <div className="persona-card__avatar">{p.name?.charAt(0) || '?'}</div>
              <div>
                <div className="persona-card__name">{p.name}</div>
                <div className="persona-card__profile">{p.profile}</div>
              </div>
              <div className="persona-card__score">
                <div className="persona-card__score-value">{p.satisfaction_score}</div>
                <div className="persona-card__score-label">/10</div>
              </div>
            </div>

            <div className="persona-card__section">
              <div className="persona-card__section-title">Motivations</div>
              <ul>{(p.motivations || []).map((m, j) => <li key={j}>{m}</li>)}</ul>
            </div>

            <div className="persona-card__section">
              <div className="persona-card__section-title persona-card__section-title--danger">Frustrations</div>
              <ul>{(p.frustrations || []).map((f, j) => <li key={j}>{f}</li>)}</ul>
            </div>

            <div className="persona-card__section">
              <div className="persona-card__section-title">Canaux</div>
              <div className="persona-card__channels">
                {(p.channels || []).map((c, j) => <span key={j} className="persona-card__channel">{c}</span>)}
              </div>
            </div>

            <div className="persona-card__reco">
              <strong>Reco :</strong> {p.recommendation}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

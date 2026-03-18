import { useRecos } from '../../api/client'

export default function RecoPanel() {
  const { data, isLoading, error } = useRecos()

  if (isLoading) return <div className="loading">Chargement...</div>
  if (error || !data) return <div className="error-msg">Erreur de chargement des recommandations.</div>

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 4 }}>
          Recommandations stratégiques
        </h2>
        <p style={{ fontSize: 12, color: 'var(--color-text-tertiary)' }}>
          Actions prioritaires pour les décideurs COMEX — synthèse du pipeline de données
        </p>
      </div>
      <div className="reco-grid">
        {data.recommendations.map(reco => (
          <div className="reco-card" key={reco.id}>
            <div className="reco-card__header">
              <span className={`reco-card__priority reco-card__priority--${reco.priority}`}>
                {reco.priority}
              </span>
              <span className="reco-card__pilier">{reco.pilier}</span>
            </div>
            <div className="reco-card__title">{reco.titre}</div>
            <div className="reco-card__desc">{reco.description}</div>
            <div className="reco-card__meta">
              <span><strong>Impact :</strong> {reco.impact}</span>
              <span><strong>Effort :</strong> {reco.effort}</span>
              <span><strong>KPI cible :</strong> {reco.kpi_cible}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

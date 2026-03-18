import { useCx } from '../../api/client'
import KpiCard from '../KpiCard'
import RatingLineChart from '../../charts/RatingLineChart'
import RatingDistBar from '../../charts/RatingDistBar'

export default function CxPanel() {
  const { data, isLoading, error } = useCx()

  if (isLoading) return <div className="loading">Chargement...</div>
  if (error || !data) return <div className="error-msg">Erreur de chargement des données CX.</div>

  const { kpis, rating_by_month, rating_distribution, irritants, enchantements, sources } = data

  return (
    <div>
      <div className="kpi-grid">
        <KpiCard
          label="Note moyenne"
          value={`${kpis.avg_rating} ★`}
          sub={`${kpis.total_reviews.toLocaleString('fr-FR')} avis`}
          variant={kpis.avg_rating >= 4 ? 'success' : kpis.avg_rating < 3 ? 'danger' : 'default'}
        />
        <KpiCard
          label="NPS proxy"
          value={kpis.nps_proxy > 0 ? `+${kpis.nps_proxy}` : `${kpis.nps_proxy}`}
          variant={kpis.nps_proxy > 20 ? 'success' : kpis.nps_proxy < 0 ? 'danger' : 'default'}
        />
        <KpiCard
          label="Total avis"
          value={kpis.total_reviews.toLocaleString('fr-FR')}
        />
        <KpiCard
          label="Avis négatifs SAV"
          value={`${Math.round(kpis.sav_negative_pct * 100)}%`}
          variant={kpis.sav_negative_pct > 0.3 ? 'danger' : 'default'}
          sub="des avis négatifs"
        />
      </div>

      <div className="chart-row">
        <div className="chart-card">
          <div className="chart-card__title">Note moyenne / mois</div>
          <RatingLineChart data={rating_by_month} />
        </div>
        <div className="chart-card">
          <div className="chart-card__title">Distribution des notes</div>
          <RatingDistBar data={rating_distribution} />
        </div>
      </div>

      <div className="chart-row">
        <div className="chart-card">
          <div className="chart-card__title">Top 5 irritants (avis 1-2★)</div>
          {irritants.length === 0
            ? <p style={{ color: 'var(--color-text-tertiary)', fontSize: 12 }}>Aucun irritant identifié.</p>
            : irritants.map((item, i) => (
              <div className="irritant-item" key={i}>
                <div className="irritant-item__header">
                  <span className="irritant-item__label">{item.label}</span>
                  <span className="irritant-item__pct">{item.pct}%</span>
                </div>
                <div className="irritant-item__track">
                  <div className="irritant-item__fill" style={{ width: `${item.bar_pct}%` }} />
                </div>
              </div>
            ))
          }
        </div>

        <div className="chart-card">
          <div className="chart-card__title">Top 3 enchantements (avis 5★)</div>
          {enchantements.length === 0
            ? <p style={{ color: 'var(--color-text-tertiary)', fontSize: 12 }}>Aucun enchantement identifié.</p>
            : enchantements.map((item, i) => (
              <div className="irritant-item" key={i}>
                <div className="irritant-item__header">
                  <span className="irritant-item__label">{item.label}</span>
                  <span className="irritant-item__pct">{item.pct}%</span>
                </div>
                <div className="irritant-item__track">
                  <div className="irritant-item__fill enchantement-item__fill" style={{ width: `${item.bar_pct}%` }} />
                </div>
              </div>
            ))
          }

          {sources.length > 0 && (
            <div style={{ marginTop: 20 }}>
              <div className="chart-card__title" style={{ marginBottom: 10 }}>Sources</div>
              {sources.map((s, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6, fontSize: 12 }}>
                  {s.url ? (
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: 'var(--color-text-info)', textDecoration: 'none' }}
                    >
                      {s.name} ↗
                    </a>
                  ) : (
                    <span style={{ color: 'var(--color-text-secondary)' }}>{s.name}</span>
                  )}
                  <span style={{ color: 'var(--color-text-tertiary)' }}>{s.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

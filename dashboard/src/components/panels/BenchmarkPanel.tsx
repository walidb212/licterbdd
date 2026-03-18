import { useBenchmark } from '../../api/client'
import KpiCard from '../KpiCard'
import SovBarChart from '../../charts/SovBarChart'
import SentimentRadar from '../../charts/SentimentRadar'

export default function BenchmarkPanel() {
  const { data, isLoading, error } = useBenchmark()

  if (isLoading) return <div className="loading">Chargement...</div>
  if (error || !data) return <div className="error-msg">Erreur de chargement des données benchmark.</div>

  const { kpis, radar, sov_by_month, brand_scores } = data

  return (
    <div>
      <div className="kpi-grid">
        <KpiCard
          label="Share of Voice — Decathlon"
          value={`${Math.round(kpis.share_of_voice_decathlon * 100)}%`}
          sub={`${kpis.total_mentions} mentions totales`}
          variant={kpis.share_of_voice_decathlon > 0.5 ? 'success' : 'default'}
        />
        <KpiCard
          label="Share of Voice — Intersport"
          value={`${Math.round(kpis.share_of_voice_intersport * 100)}%`}
        />
        <KpiCard
          label="Sentiment positif Decathlon"
          value={`${Math.round(kpis.sentiment_decathlon_positive_pct * 100)}%`}
          variant="success"
        />
        <KpiCard
          label="Sentiment positif Intersport"
          value={`${Math.round(kpis.sentiment_intersport_positive_pct * 100)}%`}
        />
      </div>

      <div className="brand-scores">
        {(['decathlon', 'intersport'] as const).map(brand => {
          const s = brand_scores[brand]
          return (
            <div className="brand-score-card" key={brand}>
              <div className={`brand-score-card__name brand-score-card__name--${brand}`}>
                <a
                  href={brand === 'decathlon' ? 'https://www.decathlon.fr' : 'https://www.intersport.fr'}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: 'inherit', textDecoration: 'none' }}
                >
                  {brand.charAt(0).toUpperCase() + brand.slice(1)} ↗
                </a>
              </div>
              <div className="brand-score-card__mention">{s.total_mentions} mentions analysées</div>
              {[
                { label: 'Positif', pct: s.positive_pct, type: 'positive' },
                { label: 'Neutre',  pct: s.neutral_pct,  type: 'neutral' },
                { label: 'Négatif', pct: s.negative_pct, type: 'negative' },
              ].map(row => (
                <div className="score-bar-row" key={row.label}>
                  <span className="score-bar-row__label">{row.label}</span>
                  <div className="score-bar-row__track">
                    <div
                      className={`score-bar-row__fill score-bar-row__fill--${row.type}`}
                      style={{ width: `${row.pct}%` }}
                    />
                  </div>
                  <span className="score-bar-row__pct">{row.pct}%</span>
                </div>
              ))}
            </div>
          )
        })}
      </div>

      <div className="chart-row">
        <div className="chart-card">
          <div className="chart-card__title">Share of Voice mensuel</div>
          <SovBarChart data={sov_by_month} />
        </div>
        <div className="chart-card">
          <div className="chart-card__title">Radar forces / faiblesses</div>
          <SentimentRadar data={radar} />
        </div>
      </div>
    </div>
  )
}

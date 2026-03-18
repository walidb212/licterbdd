import { useReputation } from '../../api/client'
import AlertBanner from '../AlertBanner'
import KpiCard from '../KpiCard'
import CrisisLineChart from '../../charts/CrisisLineChart'
import PlatformPieChart from '../../charts/PlatformPieChart'

export default function ReputationPanel() {
  const { data, isLoading, error } = useReputation()

  if (isLoading) return <div className="loading">Chargement...</div>
  if (error || !data) return <div className="error-msg">Erreur de chargement des données de réputation.</div>

  const { kpis, alert, volume_by_day, platform_breakdown, top_items } = data

  // Volume trend: last 7 days vs previous 7 days
  const last7 = volume_by_day.slice(-7).reduce((s, d) => s + d.volume, 0)
  const prev7 = volume_by_day.slice(-14, -7).reduce((s, d) => s + d.volume, 0)
  const volumeDelta = prev7 > 0 ? Math.round((last7 - prev7) / prev7 * 100) : null

  return (
    <div>
      {alert.active && (
        <AlertBanner message={alert.message} gravityScore={alert.gravity_score} />
      )}

      <div className="kpi-grid">
        <KpiCard
          label="Volume mentions"
          value={kpis.volume_total.toLocaleString('fr-FR')}
          delta={volumeDelta ?? undefined}
          deltaLabel={volumeDelta != null ? `${volumeDelta > 0 ? '+' : ''}${volumeDelta}% vs 7j préc.` : undefined}
          sub={volumeDelta == null ? 'toutes plateformes' : undefined}
        />
        <KpiCard
          label="Sentiment négatif"
          value={`${Math.round(kpis.sentiment_negatif_pct * 100)}%`}
          variant={kpis.sentiment_negatif_pct > 0.7 ? 'danger' : 'default'}
        />
        <KpiCard
          label="Gravity Score"
          value={kpis.gravity_score}
          sub="/ 10"
          variant={kpis.gravity_score > 6 ? 'danger' : kpis.gravity_score > 3 ? 'warning' : 'default'}
        />
        <KpiCard
          label="Influenceurs détracteurs"
          value={kpis.influenceurs_detracteurs}
          sub="comptes vérifiés"
        />
      </div>

      <div className="chart-row">
        <div className="chart-card">
          <div className="chart-card__title">Volume / jour</div>
          <CrisisLineChart data={volume_by_day} />
        </div>
        <div className="chart-card">
          <div className="chart-card__title">Répartition plateforme</div>
          <PlatformPieChart data={platform_breakdown} />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 16px', marginTop: 12 }}>
            {platform_breakdown.map(p => {
              const links: Record<string, string> = {
                'Reddit': 'https://www.reddit.com/search/?q=decathlon',
                'YouTube': 'https://www.youtube.com/results?search_query=decathlon',
                'TikTok': 'https://www.tiktok.com/search?q=decathlon',
                'Twitter/X': 'https://x.com/search?q=decathlon',
                'Presse': 'https://news.google.com/search?q=decathlon',
              }
              const href = links[p.platform]
              return href ? (
                <a key={p.platform} href={href} target="_blank" rel="noopener noreferrer"
                   style={{ fontSize: 11, color: 'var(--color-text-info)', textDecoration: 'none' }}>
                  {p.platform} ({p.pct}%) ↗
                </a>
              ) : null
            })}
          </div>
        </div>
      </div>

      {top_items.length > 0 && (
        <div className="chart-card">
          <div className="chart-card__title">Top signaux prioritaires</div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Entité / Signal</th>
                <th>Source</th>
                <th>Reach</th>
                <th>Sentiment</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {top_items.map((item, i) => {
                const displayText = item.summary || ''
                return (
                  <tr key={i}>
                    <td style={{ maxWidth: 360 }}>
                      {item.url ? (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ fontWeight: 600, color: 'var(--color-text-info)', textDecoration: 'none' }}
                        >
                          {item.entity} ↗
                        </a>
                      ) : (
                        <span style={{ fontWeight: 600 }}>{item.entity}</span>
                      )}
                      {displayText && (
                        <div style={{ color: 'var(--color-text-secondary)', fontSize: 11, marginTop: 2 }}>
                          {displayText.length > 100 ? displayText.slice(0, 100) + '…' : displayText}
                        </div>
                      )}
                      {item.evidence?.map((e, j) => (
                        <div key={j} style={{ fontStyle: 'italic', fontSize: 10, color: 'var(--color-text-tertiary)', marginTop: 2 }}>
                          « {e} »
                        </div>
                      ))}
                    </td>
                    <td style={{ color: 'var(--color-text-tertiary)', whiteSpace: 'nowrap' }}>{item.source}</td>
                    <td style={{ color: 'var(--color-text-tertiary)', whiteSpace: 'nowrap', fontSize: 11 }}>
                      {item.followers ? item.followers.toLocaleString('fr-FR') : '—'}
                    </td>
                    <td>
                      <span className={`badge badge--${item.sentiment}`}>{item.sentiment}</span>
                    </td>
                    <td style={{ color: 'var(--color-text-warning)', fontWeight: 600 }}>{item.priority}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

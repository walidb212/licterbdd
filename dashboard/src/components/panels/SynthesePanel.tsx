import { useSummary } from '../../api/client'

const PARTITION_COLORS: Record<string, string> = {
  social: 'var(--color-text-info)',
  news: 'var(--color-text-warning)',
  employee: 'var(--color-text-tertiary)',
  store: 'var(--color-success)',
  customer: 'var(--color-success)',
}

function formatFlag(flag: string) {
  return flag.replace(/_/g, ' ')
}

export default function SynthesePanel() {
  const { data, isLoading, error } = useSummary()

  if (isLoading) return (
    <div className="kpi-grid">
      {[1, 2, 3, 4].map(i => <div key={i} className="skeleton" style={{ height: 80 }} />)}
    </div>
  )
  if (error || !data) return <div className="error-msg">Erreur de chargement de la synthèse.</div>

  const { entities, top_risks, top_opportunities } = data

  return (
    <div>
      {/* Top Risques + Opportunités */}
      <div className="chart-row">
        <div className="chart-card">
          <div className="chart-card__title">Top Risques identifiés</div>
          {top_risks.length === 0
            ? <p style={{ color: 'var(--color-text-tertiary)', fontSize: 12 }}>Aucun risque agrégé.</p>
            : top_risks.map((r, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <span style={{
                  background: 'var(--color-background-danger)',
                  color: 'var(--color-text-danger)',
                  borderRadius: 4,
                  padding: '2px 8px',
                  fontSize: 11,
                  minWidth: 28,
                  textAlign: 'center',
                  fontWeight: 700,
                }}>{r.count}</span>
                <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>{formatFlag(r.flag)}</span>
              </div>
            ))
          }
        </div>

        <div className="chart-card">
          <div className="chart-card__title">Top Opportunités identifiées</div>
          {top_opportunities.length === 0
            ? <p style={{ color: 'var(--color-text-tertiary)', fontSize: 12 }}>Aucune opportunité agrégée.</p>
            : top_opportunities.map((o, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <span style={{
                  background: 'var(--color-background-success)',
                  color: 'var(--color-text-success)',
                  borderRadius: 4,
                  padding: '2px 8px',
                  fontSize: 11,
                  minWidth: 28,
                  textAlign: 'center',
                  fontWeight: 700,
                }}>{o.count}</span>
                <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>{formatFlag(o.flag)}</span>
              </div>
            ))
          }
        </div>
      </div>

      {/* Entities table */}
      {entities.length > 0 && (
        <div className="chart-card">
          <div className="chart-card__title">Entités clés — synthèse IA ({entities.length})</div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Entité</th>
                <th>Source</th>
                <th style={{ textAlign: 'center' }}>Vol.</th>
                <th>Risques</th>
                <th>Opportunités</th>
                <th>Takeaway IA</th>
              </tr>
            </thead>
            <tbody>
              {entities.map((e, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>{e.name}</td>
                  <td>
                    <span style={{
                      fontSize: 10,
                      padding: '2px 6px',
                      borderRadius: 3,
                      border: `1px solid ${PARTITION_COLORS[e.partition] ?? 'var(--color-border-tertiary)'}`,
                      color: PARTITION_COLORS[e.partition] ?? 'var(--color-text-tertiary)',
                      whiteSpace: 'nowrap',
                    }}>
                      {e.partition}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center', color: 'var(--color-text-tertiary)' }}>{e.volume}</td>
                  <td style={{ maxWidth: 180 }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      {e.risks.map((r, j) => (
                        <span key={j} style={{
                          fontSize: 10,
                          padding: '1px 5px',
                          borderRadius: 3,
                          background: 'var(--color-background-danger)',
                          color: 'var(--color-text-danger)',
                        }}>{formatFlag(r)}</span>
                      ))}
                    </div>
                  </td>
                  <td style={{ maxWidth: 180 }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      {e.opportunities.map((o, j) => (
                        <span key={j} style={{
                          fontSize: 10,
                          padding: '1px 5px',
                          borderRadius: 3,
                          background: 'var(--color-background-success)',
                          color: 'var(--color-text-success)',
                        }}>{formatFlag(o)}</span>
                      ))}
                    </div>
                  </td>
                  <td style={{ maxWidth: 300, color: 'var(--color-text-secondary)', fontSize: 11 }}>
                    {e.takeaway.length > 120 ? e.takeaway.slice(0, 120) + '…' : e.takeaway}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

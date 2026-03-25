import { Router } from 'express';
import { getDb, parseJsonCol } from '../db.mjs';

const router = Router();

router.get('/summary', (req, res) => {
  const db = getDb();

  const entities = db.prepare('SELECT * FROM entity_summaries ORDER BY volume_items DESC LIMIT 20')
    .all().map(r => parseJsonCol(r, 'top_themes', 'top_risks', 'top_opportunities'));

  const social = db.prepare('SELECT risk_flags, opportunity_flags FROM social_enriched').all();
  const news = db.prepare('SELECT risk_flags, opportunity_flags FROM news_enriched').all();
  const all = [...social, ...news];

  const riskCounter = {};
  const oppCounter = {};
  for (const r of all) {
    let risks, opps;
    try { risks = typeof r.risk_flags === 'string' ? JSON.parse(r.risk_flags) : (r.risk_flags || []); } catch { risks = []; }
    try { opps = typeof r.opportunity_flags === 'string' ? JSON.parse(r.opportunity_flags) : (r.opportunity_flags || []); } catch { opps = []; }
    for (const f of risks) riskCounter[f] = (riskCounter[f] || 0) + 1;
    for (const f of opps) oppCounter[f] = (oppCounter[f] || 0) + 1;
  }

  const topRisks = Object.entries(riskCounter).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([flag, count]) => ({ flag, count }));
  const topOpps = Object.entries(oppCounter).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([flag, count]) => ({ flag, count }));

  res.json({
    entities: entities.map(e => ({
      name: e.entity_name || '—',
      partition: e.source_partition || '',
      brand: e.brand_focus || 'both',
      volume: e.volume_items || 0,
      themes: (e.top_themes || []).slice(0, 3),
      risks: (e.top_risks || []).slice(0, 3),
      opportunities: (e.top_opportunities || []).slice(0, 3),
      takeaway: e.executive_takeaway || '',
    })),
    top_risks: topRisks,
    top_opportunities: topOpps,
  });
});

export default router;

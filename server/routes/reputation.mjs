import { Router } from 'express';
import { getDb, parseJsonCol } from '../db.mjs';
import { gravityScore, platformFromSourceName, volumeByDay } from '../kpis.mjs';

const router = Router();

router.get('/reputation', (req, res) => {
  const db = getDb();

  const social = db.prepare('SELECT * FROM social_enriched').all().map(r => parseJsonCol(r, 'themes', 'risk_flags', 'opportunity_flags', 'evidence_spans'));
  const news = db.prepare('SELECT * FROM news_enriched').all().map(r => parseJsonCol(r, 'themes', 'risk_flags', 'opportunity_flags', 'evidence_spans'));
  const excelRep = db.prepare('SELECT * FROM excel_reputation').all().map(r => ({
    ...r,
    sentiment_label: (r.sentiment || 'negative').toLowerCase(),
    published_at: r.date || '',
    source_name: r.platform || '',
    priority_score: null,
  }));

  const all = [...social, ...news, ...excelRep];
  const total = all.length;
  const negCount = all.filter(r => r.sentiment_label === 'negative').length;
  const negPct = total ? Math.round(negCount / total * 1000) / 1000 : 0;
  const gscore = gravityScore(all);

  const detractors = all.filter(r =>
    r.sentiment_label === 'negative' && [true, 'True', 'true', 1, '1'].includes(r.is_verified)
  ).length;

  const vbd = volumeByDay(all);

  // Platform breakdown
  const platformCounts = {};
  for (const r of all) {
    const p = platformFromSourceName(r.source_name || r.platform || r._sheet || '');
    platformCounts[p] = (platformCounts[p] || 0) + 1;
  }
  const platformTotal = Object.values(platformCounts).reduce((a, b) => a + b, 0) || 1;
  const platformBreakdown = Object.entries(platformCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([platform, count]) => ({ platform, count, pct: Math.round(count / platformTotal * 100) }));

  // Top items
  const topItems = all
    .filter(r => r.priority_score != null)
    .sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0))
    .slice(0, 10)
    .map(r => ({
      entity: r.entity_name || r.user_name || r.author || '—',
      summary: r.summary_short || (r.text || '').slice(0, 120),
      priority: r.priority_score,
      sentiment: r.sentiment_label || 'neutral',
      source: platformFromSourceName(r.source_name || r.platform || ''),
      followers: r.followers || null,
      url: null,
      evidence: (r.evidence_spans || []).slice(0, 2),
    }));

  const alertActive = gscore > 6 || negPct > 0.70;

  res.json({
    kpis: { volume_total: total, sentiment_negatif_pct: negPct, gravity_score: gscore, influenceurs_detracteurs: detractors },
    volume_by_day: vbd,
    platform_breakdown: platformBreakdown,
    top_items: topItems,
    alert: { active: alertActive, gravity_score: gscore, message: alertActive ? 'Crise active — Vélo défectueux' : 'Situation normale' },
  });
});

export default router;

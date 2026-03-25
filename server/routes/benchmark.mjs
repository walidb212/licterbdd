import { Router } from 'express';
import { getDb, parseJsonCol } from '../db.mjs';
import { radarTopics, sov, sovByMonth } from '../kpis.mjs';

const router = Router();

router.get('/benchmark', (req, res) => {
  const db = getDb();

  const social = db.prepare('SELECT * FROM social_enriched').all().map(r => parseJsonCol(r, 'themes'));
  const excelBench = db.prepare('SELECT * FROM excel_benchmark').all().map(r => {
    let brandFocus = '';
    const brand = (r.brand || '').toLowerCase();
    if (brand.includes('intersport')) brandFocus = 'intersport';
    else if (brand.includes('decathlon')) brandFocus = 'decathlon';
    return {
      ...r,
      brand_focus: brandFocus,
      sentiment_label: r.sentiment_detected || 'neutral',
      themes: [],
    };
  });

  const all = [...social, ...excelBench];
  const branded = all.filter(r => r.brand_focus === 'decathlon' || r.brand_focus === 'intersport');

  const sovData = sov(branded);
  const decRecords = branded.filter(r => r.brand_focus === 'decathlon');
  const intRecords = branded.filter(r => r.brand_focus === 'intersport');

  const posPct = (records) => {
    if (!records.length) return 0;
    return Math.round(records.filter(r => r.sentiment_label === 'positive').length / records.length * 1000) / 1000;
  };

  const brandSummary = (records) => {
    const total = records.length;
    const pos = records.filter(r => r.sentiment_label === 'positive').length;
    const neg = records.filter(r => r.sentiment_label === 'negative').length;
    return {
      total_mentions: total,
      positive_pct: total ? Math.round(pos / total * 100) : 0,
      negative_pct: total ? Math.round(neg / total * 100) : 0,
      neutral_pct: total ? Math.round((total - pos - neg) / total * 100) : 0,
    };
  };

  res.json({
    kpis: {
      share_of_voice_decathlon: sovData.decathlon,
      share_of_voice_intersport: sovData.intersport,
      sentiment_decathlon_positive_pct: posPct(decRecords),
      sentiment_intersport_positive_pct: posPct(intRecords),
      total_mentions: branded.length,
    },
    radar: radarTopics(branded),
    sov_by_month: sovByMonth(branded),
    brand_scores: { decathlon: brandSummary(decRecords), intersport: brandSummary(intRecords) },
  });
});

export default router;

import { Router } from 'express';
import { getDb, parseJsonCol } from '../db.mjs';
import { enchantements, irritants, npsProxy, ratingByMonth, ratingDistribution } from '../kpis.mjs';

const router = Router();

router.get('/cx', (req, res) => {
  const db = getDb();

  const reviewEnriched = db.prepare("SELECT * FROM review_enriched WHERE source_partition != 'employee'")
    .all().map(r => parseJsonCol(r, 'themes'));
  const storeReviews = db.prepare('SELECT * FROM store_reviews').all().map(r => parseJsonCol(r, 'themes'));
  const excelCx = db.prepare('SELECT * FROM excel_cx').all().map(r => ({
    ...r,
    published_at: r.date || '',
    sentiment_label: (r.sentiment || '').toLowerCase(),
    themes: [],
  }));

  const allReviews = [...storeReviews, ...reviewEnriched, ...excelCx];

  // Avg rating
  const ratings = [];
  for (const r of allReviews) {
    const v = parseFloat(r.rating || r.note || 0);
    if (v >= 1 && v <= 5) ratings.push(v);
  }
  const avgRating = ratings.length ? Math.round(ratings.reduce((a, b) => a + b, 0) / ratings.length * 100) / 100 : 0;
  const nps = npsProxy(allReviews);

  // SAV negative pct
  const savThemes = new Set(['service_client', 'retour_remboursement']);
  const savNeg = allReviews.filter(r =>
    r.sentiment_label === 'negative' && (r.themes || []).some(t => savThemes.has(t))
  ).length;
  const savNegPct = allReviews.length ? Math.round(savNeg / allReviews.length * 1000) / 1000 : 0;

  const rbm = ratingByMonth(allReviews);
  const dist = ratingDistribution(allReviews);

  const enriched = [...reviewEnriched, ...storeReviews.filter(r => r.themes?.length)];
  const irr = irritants(enriched, 5);
  const ench = enchantements(enriched, 3);

  // Sources
  const sourceData = {};
  for (const r of allReviews) {
    const name = r.source_name || r.platform || r.site || 'Autre';
    if (!sourceData[name]) sourceData[name] = { count: 0, url: null };
    sourceData[name].count++;
    if (!sourceData[name].url) sourceData[name].url = r.source_url || r.google_maps_url || null;
  }
  const sources = Object.entries(sourceData)
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, 8)
    .map(([name, v]) => ({ name, count: v.count, url: v.url }));

  res.json({
    kpis: { avg_rating: avgRating, nps_proxy: nps, total_reviews: allReviews.length, sav_negative_pct: savNegPct },
    rating_by_month: rbm,
    rating_distribution: dist,
    irritants: irr,
    enchantements: ench,
    sources,
  });
});

export default router;
